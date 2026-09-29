import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils import player
from app.database.repository import MediaRepository


class PlayerTests(unittest.TestCase):
    def test_priorities_and_manual_choices(self):
        for system in ('Linux', 'Darwin', 'Windows'):
            with patch.object(player.platform, 'system', return_value=system):
                for installed in ({}, {'vlc': '/vlc'}, {'mpv': '/mpv'}, {'mpv': '/mpv', 'vlc': '/vlc'}):
                    with self.subTest(system=system, installed=installed):
                        expected = ('mpv' if system == 'Linux' and 'mpv' in installed
                                    else 'vlc' if 'vlc' in installed else 'system')
                        self.assertEqual(player.get_preferred_player(None, installed), expected)
                        self.assertEqual(player.get_preferred_player('auto', installed), expected)
                        for choice in ('mpv', 'vlc', 'system', 'unknown'):
                            self.assertEqual(player.get_preferred_player(choice, installed),
                                             choice if choice in installed else 'system')

    def test_linux_detection_and_options(self):
        with patch.object(player.platform, 'system', return_value='Linux'):
            for installed in ({}, {'mpv': '/bin/mpv'}, {'vlc': '/bin/vlc'},
                              {'mpv': '/bin/mpv', 'vlc': '/bin/vlc'}):
                with patch.object(player.shutil, 'which', side_effect=installed.get):
                    self.assertEqual(player.detect_players(), installed)
                    self.assertEqual(player.get_available_players(), ['auto', *installed, 'system'])

    def test_native_install_locations(self):
        for system, expected in (('Darwin', '/Applications/VLC.app/Contents/MacOS/VLC'),
                                 ('Windows', 'C:/Program Files/VideoLAN/VLC/vlc.exe')):
            with patch.object(player.platform, 'system', return_value=system), \
                 patch.object(player.Path, 'is_file', return_value=True), \
                 patch.object(player.os, 'access', return_value=True), \
                 patch.dict(player.os.environ, {'ProgramW6432': 'C:/Program Files'}):
                self.assertEqual(player.find_vlc(), expected)
        for system in ('Darwin', 'Windows'):
            with patch.object(player.platform, 'system', return_value=system), \
                 patch.object(player.shutil, 'which', return_value=None), \
                 patch.object(player.Path, 'is_file', return_value=True), \
                 patch.object(player.os, 'access', return_value=True), \
                 patch.dict(player.os.environ, {'ProgramW6432': 'C:/Program Files'}):
                self.assertIsNotNone(player.find_mpv())

    def test_launch_arguments_and_subtitles(self):
        with tempfile.TemporaryDirectory() as directory:
            media = Path(directory) / "Film é & ' spécial.mp4"
            media.touch()
            subtitle = media.with_suffix('.srt')
            subtitle.touch()
            for choice in ('mpv', 'vlc'):
                with patch.object(player, 'detect_players', return_value={choice: '/player path'}), \
                     patch.object(player.subprocess, 'Popen') as popen:
                    player.open_media(str(media), choice)
                    expected = (['/player path', '--fullscreen', '--sub-file=' + str(subtitle), str(media)]
                                if choice == 'mpv' else
                                ['/player path', '--fullscreen', str(media), '--sub-file', str(subtitle)])
                    popen.assert_called_once_with(expected)

    def test_system_fallbacks(self):
        for system, command in (('Linux', 'xdg-open'), ('Darwin', 'open'), ('Windows', None)):
            for choice in ('auto', 'mpv', 'vlc', 'system'):
                with patch.object(player.platform, 'system', return_value=system), \
                     patch.object(player, 'detect_players', return_value={}), \
                     patch.object(player.subprocess, 'Popen') as popen, \
                     patch.object(player.os, 'startfile', create=True) as startfile:
                    media = Path('/tmp/film é.mp4').absolute()
                    player.open_media(media, choice)
                    if command:
                        popen.assert_called_once_with([command, str(media)])
                    else:
                        startfile.assert_called_once_with(str(media))
                        popen.assert_not_called()

    def test_launch_failure_falls_back_and_system_error_propagates(self):
        with patch.object(player.platform, 'system', return_value='Linux'), \
             patch.object(player, 'detect_players', return_value={'mpv': '/mpv'}), \
             patch.object(player, 'find_subtitle', return_value=None), \
             patch.object(player.subprocess, 'Popen', side_effect=[PermissionError(), None]) as popen:
            player.open_media('/tmp/movie.mp4', 'mpv')
            self.assertEqual(popen.call_args.args[0], ['xdg-open', '/tmp/movie.mp4'])
            popen.side_effect = OSError('cannot start')
            with self.assertRaises(OSError):
                player.open_media('/tmp/movie.mp4', 'mpv')

    def test_preference_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'media.db'
            repository = MediaRepository(database)
            self.assertIsNone(repository.get_setting('video_player'))
            for choice in ('auto', 'mpv', 'vlc', 'system'):
                repository.set_setting('video_player', choice)
                self.assertEqual(MediaRepository(database).get_setting('video_player'), choice)


class PlaybackEntryPointTests(unittest.TestCase):
    def test_both_entry_points_use_shared_handler(self):
        from unittest.mock import Mock
        from app.ui.main_window import MainWindow, FullscreenEntryDialog
        window = Mock()
        window.current_entry.kind = 'movie'
        window.current_item.filepath = Path('/tmp/movie.mp4')
        MainWindow.play_current(window)
        window.play_video.assert_called_once_with(window.current_item.filepath)
        dialog = Mock()
        dialog.entry.kind = 'movie'
        dialog.entry.items = [window.current_item]
        FullscreenEntryDialog.watch_entry(dialog)
        dialog.parent().play_video.assert_called_once_with(window.current_item.filepath)

    def test_shared_handler_reads_preference_and_reports_errors(self):
        from unittest.mock import Mock
        from app.ui.main_window import MainWindow
        window = Mock()
        window.repository.get_setting.return_value = 'mpv'
        with patch('app.ui.main_window.open_media') as launch, \
             patch('app.ui.main_window.QMessageBox.warning') as warning:
            MainWindow.play_video(window, '/tmp/movie.mp4')
            launch.assert_called_once_with('/tmp/movie.mp4', 'mpv')
            launch.side_effect = OSError('Unavailable')
            MainWindow.play_video(window, '/tmp/movie.mp4')
            warning.assert_called_once()


class SubtitleSelectionTests(unittest.TestCase):
    def select(self, filenames, video='Film.mp4', expected=None):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in filenames:
                (folder / name).touch()
            result = player.find_subtitle(folder / video)
            self.assertEqual(result, folder / expected if expected else None)

    def test_french_preferred_to_exact_and_english(self):
        self.select(['Film.srt', 'Film.en.srt', 'Film.fr.srt'], expected='Film.fr.srt')

    def test_french_markers_case_and_separators(self):
        for marker in ('fr', 'FR', 'Fr', 'fR', 'french', 'FRENCH', 'French'):
            for separator in ('.', '-', '_'):
                name = 'Film' + separator + marker + '.srt'
                with self.subTest(name=name):
                    self.select(['Film.srt', name], expected=name)

    def test_french_letters_inside_words_are_not_markers(self):
        self.select(['Film.friends.srt', 'Film-afraid.srt', 'Film_frenchman.srt'])
        self.select(['Film.friends.srt', 'Film.srt'], expected='Film.srt')
        self.select(['Afrique.en.srt', 'Afrique.srt'], video='Afrique.mp4', expected='Afrique.srt')

    def test_only_matching_episode_is_selected(self):
        self.select(['Serie.S01E01.fr.srt', 'Serie.S01E02.fr.srt', 'Serie.S01E03.fr.srt'],
                    video='Serie.S01E02.mp4', expected='Serie.S01E02.fr.srt')

    def test_unrelated_subtitles_are_never_selected(self):
        self.select(['Serie.S01E01.fr.srt', 'Serie.S01E03.fr.srt', 'AutreFilm.srt',
                     'Serie.S01E020.fr.srt', 'Serie.S01E02.extra.fr.srt'],
                    video='Serie.S01E02.mp4')
        self.select([])
        self.select(['Film.en.srt'])

    def test_supported_extensions_and_deterministic_priority(self):
        for extension in player.SUBTITLE_EXTENSIONS:
            with self.subTest(extension=extension):
                name = 'Film.FR' + extension.upper()
                self.select(['Film.srt', name], expected=name)
        self.select(['Film.fr.vtt', 'Film.fr.srt', 'Film.fr.ass'], expected='Film.fr.srt')
        self.select(['Film.vtt', 'Film.ass'], expected='Film.ass')

    def test_directories_and_unsupported_extensions_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'Film.fr.srt').mkdir()
            (folder / 'Film.fr.txt').touch()
            self.assertIsNone(player.find_subtitle(folder / 'Film.mp4'))

    def test_mpv_and_vlc_receive_only_selected_subtitle(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            media = folder / 'Film.mp4'
            unrelated = folder / 'AutreFilm.fr.srt'
            unrelated.touch()
            for french in (False, True):
                subtitle = folder / 'Film.FR.srt'
                if french:
                    subtitle.touch()
                for choice in ('mpv', 'vlc'):
                    with self.subTest(french=french, player=choice), \
                         patch.object(player, 'detect_players', return_value={choice: '/player'}), \
                         patch.object(player.subprocess, 'Popen') as popen:
                        player.open_media(media, choice)
                        command = popen.call_args.args[0]
                        if french:
                            self.assertIn('--sub-file=' + str(subtitle) if choice == 'mpv'
                                          else str(subtitle), command)
                        else:
                            self.assertEqual(command, ['/player', '--fullscreen', str(media)])
                        self.assertNotIn(str(unrelated), command)

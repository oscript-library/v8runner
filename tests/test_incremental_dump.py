import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / 'src' / 'v8runner.os'


@unittest.skipUnless(shutil.which('oscript'), 'OneScript is required')
class IncrementalDumpTest(unittest.TestCase):
    def check_response(self, response, expected, versions=True, explicit=False,
                       raise_errors=True, allow_empty=True):
        source = SOURCE.read_text(encoding='utf-8-sig')
        start = source.index('Функция ПроверитьВозможностьОбновленияФайловВыгрузки(')
        end = source.index('КонецФункции', start) + len('КонецФункции')
        with tempfile.TemporaryDirectory(prefix='v8runner-incremental-') as directory:
            root = Path(directory)
            if versions:
                (root / 'ConfigDumpInfo.xml').touch()
            reference = root / ('ConfigDumpInfo.xml' if versions else 'reference.xml')
            if explicit:
                reference.touch()
            if response is not None:
                (root / 'response.txt').write_bytes(response)
            harness = '''#Использовать tempfiles
#Использовать logos
Перем Лог;
Перем мИсключениеПриОшибкеВыполненияКоманды;

Процедура ВыгрузитьИзмененияКонфигурацииВФайл(Каталог, Путь, Версии, Формат)
	Если Новый Файл("response.txt").Существует() Тогда
		КопироватьФайл("response.txt", Путь);
	КонецЕсли;
КонецПроцедуры

'''
            harness += source[start:end]
            harness += '''
Лог = Логирование.ПолучитьЛог("test.incremental");
мИсключениеПриОшибкеВыполненияКоманды = АргументыКоманднойСтроки[1] = "raise";
Результат = ПроверитьВозможностьОбновленияФайловВыгрузки(ТекущийКаталог(), АргументыКоманднойСтроки[0], "", АргументыКоманднойСтроки[2] = "allow");
Сообщить(?(Результат, "INCREMENTAL", "FULL"));
'''
            script = root / 'check.os'
            script.write_text(harness, encoding='utf-8-sig')
            env = os.environ.copy()
            env.pop('OSLIB_LOADER_DUPLICATES', None)
            result = subprocess.run(
                ['oscript', str(script), str(reference) if explicit else '',
                 'raise' if raise_errors else 'ignore', 'allow' if allow_empty else 'deny'],
                cwd=root, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), expected)

    def test_empty_response(self):
        self.check_response(b'', 'INCREMENTAL')

    def test_bom_only_response(self):
        self.check_response(b'\xef\xbb\xbf', 'INCREMENTAL', explicit=True)

    def test_modified(self):
        self.check_response(b'Modified:Configuration.Test\r\n', 'INCREMENTAL')

    def test_new(self):
        self.check_response(b'New:Catalog.Test\r\n', 'INCREMENTAL')

    def test_full_dump(self):
        self.check_response(b'FullDump\r\n', 'FULL')

    def test_full_dump_case_insensitive(self):
        self.check_response(b'fulldump\r\n', 'FULL')

    def test_missing_response(self):
        self.check_response(None, 'FULL')

    def test_missing_versions(self):
        self.check_response(b'', 'FULL', versions=False)

    def test_external_reference_without_local_versions(self):
        self.check_response(b'', 'INCREMENTAL', versions=False, explicit=True)

    def test_empty_response_with_suppressed_errors_stays_full(self):
        self.check_response(b'', 'FULL', raise_errors=False)

    def test_empty_response_for_extension_stays_full(self):
        self.check_response(b'', 'FULL', allow_empty=False)

    def check_command(self, relative_versions, expected_external):
        source = SOURCE.read_text(encoding='utf-8-sig')
        start = source.index('Процедура ВыгрузитьКонфигурациюВФайлы(')
        end = source.index('КонецПроцедуры', start) + len('КонецПроцедуры')
        harness = '''Перем РежимВыгрузкиКонфигурации;
Функция СтандартныеПараметрыЗапускаКонфигуратора()
	Возврат Новый Массив;
КонецФункции
Функция ОбернутьВКавычки(Значение)
	Возврат Значение;
КонецФункции
Функция ИспользуемаяВерсияПлатформыСтаршеИлиРавна(Версия)
	Возврат Истина;
КонецФункции
Функция ПроверитьВозможностьОбновленияФайловВыгрузки(Каталог, Версии, Формат, ПустойОтвет)
	Возврат Истина;
КонецФункции
Процедура ВыполнитьКоманду(Параметры)
	Для Каждого Параметр Из Параметры Цикл
		Сообщить(Параметр);
	КонецЦикла;
КонецПроцедуры
'''
        harness += source[start:end]
        harness += '\nВыгрузитьКонфигурациюВФайлы(ТекущийКаталог(), "Hierarchical", Истина, АргументыКоманднойСтроки[0]);\n'
        with tempfile.TemporaryDirectory(prefix='v8runner-command-') as directory:
            root = Path(directory)
            script = root / 'command.os'
            script.write_text(harness, encoding='utf-8-sig')
            versions = str(root / 'ConfigDumpInfo.xml') if relative_versions is None else relative_versions
            result = subprocess.run(['oscript', str(script), versions], cwd=root,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('-update', result.stdout.splitlines())
            self.assertEqual('-configDumpInfoForChanges' in result.stdout, expected_external)

    def test_same_absolute_versions_update_in_place(self):
        self.check_command(None, False)

    def test_same_relative_versions_update_in_place(self):
        self.check_command('ConfigDumpInfo.xml', False)

    def test_external_versions_retained(self):
        self.check_command('../reference/ConfigDumpInfo.xml', True)

    def test_implicit_versions_update_in_place(self):
        self.check_command('', False)


if __name__ == '__main__':
    unittest.main()

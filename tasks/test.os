#Использовать 1testrunner

Процедура ПровестиТестирование()
	
	Тестер = Новый Тестер;

	КаталогПроекта = ОбъединитьПути(ТекущийСценарий().Каталог, "..");
	
	ФайлРезультатовТестовПакета = Новый Файл(ОбъединитьПути(КаталогПроекта,"test-reports" , "tests.xml"));
	КаталогТестов = Новый Файл(ОбъединитьПути(КаталогПроекта, "tests"));

	РезультатТестирования = Тестер.ТестироватьКаталог(КаталогТестов, ФайлРезультатовТестовПакета);

КонецПроцедуры


ПровестиТестирование();
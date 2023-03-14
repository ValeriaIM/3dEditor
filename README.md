# 3D-Editor

Автор: Мухаметдинова Валерия\
Версия: 1.1

## Описание:
Это программа предполагает графический интерфейс с возможность создания трехмерных плоскостей и многогранников, 
с помощью опорных точек, создание срезов трехмерных фигур.
Но пока она может только создавать точки и прямые с помощью уже существующих точек.

## Требования:
* Python версии не ниже 3.6
* PyQt5 с установленным QtWebKit (для *nix-систем нужно устанавливать отдельно) для запуска графической версии

## Запуск: 
`python main.py`

## Состав:
* файл запуска: `main.py`
* Модули: `editor/`
* Изображения: `pictures`
* Элементы: `sourse/`

## Описание разделов меню
При открытии вы можете увидеть поле для создания фигур и 
меню создания основных элементов: точка и линия
(Их также можно быстро выбрать, нажав `1` и `2` соответственно)

Чтобы создать точку: выберите ее из меню и поставьте в любом месте на поле
Чтобы создать прямую: выберите ее из меню, нажмите поочередно на 
две точки, которые вы хотите соединить.

Также вы можете управлять полем, совершая повороты.
Поворот можно сделать с помощью клавиш (`W`, `A`, `S`, `D`, `R`)
Сверху в контекстном меню во вкладке `Rotates` также можно посмотреть, какой именно поворот происходит.

Сверху есть контекстное меню, где помимо вкладки `Rotates` есть вкладка `Modes` в которой вы можете выбрать режимы модерации. 
Пока он только один - `View`. С помощью него вы можете двигать поле.
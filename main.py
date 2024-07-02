# Гоночный автомобиль приезжает на пит-стоп. Автомобиль обслуживают 5 работников,
# каждый из которых выполняет определенную (любую, на ваше усмотрение) работу.
# Проблема в том, что приступить к обслуживанию они могут только все вместе,
# но после отъезда автомобиля работникам требуется некоторое псевдослучайное время для того,
# чтобы подготовиться к обслуживанию следующего.
# Автомобиль же приезжает на пит-стоп вне зависимости от готовности работников,
# и по приезду автоматически запускает таймер пит-стопа.
# Как только работники закончат, таймер останавливается и выводится, а автомобиль уезжает.
# Программа завершается, когда автомобили перестают приезжать на пит-стоп,
# и работники дожидались некоторое время, но не дождались больше ни одного автомобиля.


# Thread - ДА (отдельный работник и автомобиль - процессы).
# Pool - нет, т.к. задача не на вычисления.
# Lock - ДА, т.к. работники могут обслуживать одновременно только одну машину,
# взятую из очереди.
# Semaphore - ДА (определить сколько машин могут стоять на питлейне).
# Event - ДА (начало гонки).
# Condition - ДА (когда место в боксах освобождается
# и первая машина в очереди начинает заезжать в них, то работники не начинают работу,
# они ждут пока машина подъедет и остановится, уведомив об этом работников).
# Barrier - ДА, т.к. "приступить к обслуживанию они могут только все вместе".
# Queue - ДА, т.к. работники могут обслуживать одновременно только одну машину,
# поэтому будет выстраиваться очередь из машин.
# Pipe - нет, т.к. никакого общения между работниками нет,
# им не нужно принимать или получать информацию друг от друга.


# Работник начинает ожидать приезда машины после того,
# как будет готов к питстопу.
# Питстоп начинается не в одно время с приездом машины.
# Машина может приехать, но не все работники будут готовы обслуживать машину.

# Какие ситкации нужно обработать:
# 1) Машина едет с питлейна в боксы,
# а в это время какой-то из работников устаёт ждать приежда машины,
# что приведёт к завершению программы,
# хотя машина ещё находится в движении.
# 2) Если машина хочет заехать на питлейн,
# но мест на питлейне больше нет, то она остаётся на трассе
# (тогда сначала будет проверка на возможность заехать на питлейн,
# а потом уже решение, заезжать или нет).


# Машина:
# Когда начнётся гонка, машина начнёт ехать.
# После проезда каждого круга машина с какой-то вероятностью заезжает на питлейн
# и начинает ожидать указания менеджера.
# Если на питлейне уже ожидает своей очереди какая-то машина,
# то наша машина становится за ней.
# Когда первая в очереди машина уезжает в боксы,
# следующая машина за ней встаёт на её место.
# Если менеджер сообщает машине, что боксы свободны, то машина заезжает в них
# (она делает это мгновенно).
# Если менеджер сообщает машине, что боксы заняты,
# то наша машина останавливается на питлейне и ждёт своей очереди.
# Если работники готовы обслужить машину, то начинается питстоп.
# Если не готовы, то машина ожидает готовности работников.
# После окончания питстопа машина покидает боксы и возвращается на трасу,
# чтобы проехать следующий круг.
# Цикл повторяется.

# Работник:
# Когда начнётся гонка, работник начнёт ожидать машину в боксах.
# Если хотя бы один из работников не дожидается машину, то программа завершается.
# Если машина заезжает в боксы, а все работники готовы обслужить машину,
# то начинается питстоп.
# После начала питстопа работник обслуживает свою часть машины.
# Когда все работники обслужат свою часть машины, питстоп закончится.
# После окончания питстопа обслуженная машина покидает боксы.
# Цикл повторяется.

# Контроллер:
# Когда начнётся гонка, контроллер начнёт ожидать машину на питлейне.
# Если на питлейне ожидает машина, то менеджер проверяет, заняты ли сейчас боксы.
# Если боксы свободны, то менеджер отправляет первую машины на питлейне в них.
# Боксы считаются свободными, если обслуженная машина покинула боксы.
# Когда машина заезжает в боксы (уехала с питлейна) и начинает ожидать питстопа,
# менеджер запускает таймер.
# Когда окончится питстоп, менеджер останавливает таймер.
# Цикл повторяется.

# Менеджер:
# Когда начнётся гонка, менеджер начнёт ожидать машину, которая поедет в боксы.
# Когда контроллер направит машину в боксы, менеджер засечёт время начала питстопа.
# Когда машина будет обслужена, менеджер остановит таймер.


from threading import Thread, Lock, Event, Condition, Barrier, BrokenBarrierError
from queue import Queue
from time import sleep, monotonic
from random import randint, random


# quantities

NUM_OF_WORKERS = 5
NUM_OF_CARS = 3
NUM_OF_LAPS = 1
NUM_OF_PITLANE_LIMIT = 1

# randoms

CAR_GO_ON_PITLANE_PERCENT = 100
LAP_TIME_MIN_PART = 3
LAP_TIME_INACCURACY_COEFF = 2
WORK_TIME_RANGE = 1, 3
PREPARE_TIME_RANGE = 1, 4
WORK_AND_PREPARE_TIME_COEFF = 4

# timeouts

WAIT_CAR_TIME = NUM_OF_LAPS * (LAP_TIME_MIN_PART + LAP_TIME_INACCURACY_COEFF)


def _format_time(time: int | float):
    def _add_zeros(time: int | float, needed_len: int):
        return f'{(needed_len - len(time)) * "0"}{time}'
    minuts = int(time // 1)
    decimal_part = round((time - minuts) * 60, 3)
    seconds = _add_zeros(str(int(decimal_part // 1)), 2)
    milliseconds = _add_zeros(str(int((decimal_part * 1000) % 1000)), 3)
    return f'{minuts}:{seconds},{milliseconds}'

class Car(Thread):
    def __init__(
            self, name: str,
            race_start: Event,
            pitlane: Queue,
            car_in_boxes: Lock,
            car_ready: Condition
        ):
        super().__init__()
        self.name = name
        self._race_start = race_start
        self._pitlane = pitlane
        self._car_in_boxes = car_in_boxes
        self._car_ready = car_ready
        self.race_time = 0

    def _drive_lap(self, lap: int):
        print(f'Машина "{self.name}" поехала на круг №{lap} (Total: {_format_time(self.race_time)} | Lap: 0:00,000)')
        lap_start = monotonic()
        sleep(LAP_TIME_MIN_PART + LAP_TIME_INACCURACY_COEFF * random())
        if not self._pitlane.full():
            print(f'\n--- На питлейне есть свободное место, ', end='')
            pitstop = 100 * random()
            if pitstop < CAR_GO_ON_PITLANE_PERCENT:
                print(f'поэтому машина "{self.name}" решила заехать на него ({_format_time(monotonic()-lap_start)}) ---\n')
                self._pitlane.put(self.name)
                with self._car_in_boxes:
                    with self._car_ready:
                        self._car_ready.wait()
                print(f'Машина "{self.name}" вернулась на трассу')
            else:
                print(f'но машина "{self.name}" решила остаться на трассе ---\n')
        else:
            print(f'--- На питлейне нет свободного места, поэтому машина "{self.name}" остаётся на трассе ---')
        lap_time = monotonic() - lap_start
        print(f'Машина "{self.name}" проехала круг №{lap} (Total: {_format_time(self.race_time + lap_time)} | Lap: {_format_time(lap_time)})\n')
        self.race_time += lap_time

    def run(self):
        self._race_start.wait()
        for i in range(NUM_OF_LAPS):
            self._drive_lap((i+1))
        print(f'\n*************************** Машина "{self.name}" завершила гонку ({_format_time(self.race_time)}) ***************************\n')


class Worker(Thread):
    def __init__(
            self, name: str,
            race_start: Event,
            team_ready: Barrier,
            is_car_ready_lock: Lock,
            car_ready: Condition,
            race_end_lock: Lock
        ):
        super().__init__()
        self.name = name
        self._race_start = race_start
        self._team_ready = team_ready
        self._is_car_ready_lock = is_car_ready_lock
        self._car_ready = car_ready
        self._race_end_lock = race_end_lock

    def run(self):
        global race_end
        global is_car_ready
        global car
        global pitstop_time_start

        self._race_start.wait()
        while True:
            try:
                self._team_ready.wait(timeout=WAIT_CAR_TIME)
            except BrokenBarrierError:
                with self._race_end_lock:
                    if race_end == False:
                        race_end = True
                        equal_quantity = int(((37 - len(self.name)) / 2) // 1) * "="
                        print('\n==============================================================================================')
                        print(f'{equal_quantity} Работник "{self.name}" не дождался машины, поэтому гонка завершена {equal_quantity}{"=" if len(self.name) % 2 == 0 else ""}')
                        print('==============================================================================================\n')
                    break
            sleep(randint(*WORK_TIME_RANGE) / WORK_AND_PREPARE_TIME_COEFF)
            print(f'Работник "{self.name}" {specializations[self.name]} для машины "{car}" ({_format_time(monotonic()-pitstop_time_start)})')
            with self._is_car_ready_lock:
                is_car_ready += 1
                if is_car_ready == 5:
                    with self._car_ready:
                        is_car_ready = 0
                        print(f'========================== ВРЕМЯ ПИТСТОПА для машины "{car}": {_format_time(monotonic()-pitstop_time_start)} ===========================\n')
                        self._car_ready.notify_all()
            sleep(randint(*PREPARE_TIME_RANGE) / WORK_AND_PREPARE_TIME_COEFF)
            print(f'(работник "{self.name}" закончил готовиться к обслуживанию следующей машины)')


class Controller(Thread):
    def __init__(
            self, race_start: Event,
            pitlane: Queue,
            boxes_closed: Lock,
            team_ready: Barrier,
            car_ready: Condition,
        ):
        super().__init__()
        self._race_start = race_start
        self._pitlane = pitlane
        self._boxes_closed = boxes_closed
        self._team_ready = team_ready
        self._car_ready = car_ready

    def run(self):
        global race_end
        global car
        global pitstop_time_start

        self._race_start.wait()
        while True:
            if race_end == True:
                break
            if not self._pitlane.empty():
                with self._boxes_closed:
                    car = self._pitlane.get()
                    print(f'\n=============================== Для машины "{car}" начался питстоп ===============================')
                    pitstop_time_start = monotonic()
                    self._team_ready.wait()
                    self._team_ready.reset()
                    with self._car_ready:
                        self._car_ready.wait()


if __name__ == '__main__':
    race_start = Event()
    pitlane = Queue(maxsize=NUM_OF_PITLANE_LIMIT)
    boxes_closed = Lock()
    car_in_boxes = Lock()
    team_ready = Barrier(NUM_OF_WORKERS+1)
    car_ready = Condition()

    race_end, race_end_lock = False, Lock()
    is_car_ready, is_car_ready_lock = 0, Lock()
    car = ''
    pitstop_time_start = 0

    car_names = ['A', 'B', 'C', 'D', 'E', 'F']
    specializations = {
        'Гайковёрт': 'поменял колёса',
        'Механик': 'проверил двигатель',
        'Мойщик': 'протёр стёкла и зеркала',
        'Второй пилот': 'заменил текущего пилота',
        'Антикрыло': 'поменял переднее антикрыло',
    }

    cars = [Car(car_names[i], race_start, pitlane, car_in_boxes, car_ready) for i in range(NUM_OF_CARS)]
    workers = [Worker(name, race_start, team_ready, is_car_ready_lock, car_ready, race_end_lock) for name in specializations.keys()]
    controller = Controller(race_start, pitlane, boxes_closed, team_ready, car_ready)

    for car in cars:
        car.start()

    for worker in workers:
        worker.start()

    controller.start()

    sleep(1)
    print('\n==============================================================================================')
    print('======================================= ГОНКА НАЧАЛАСЬ =======================================')
    print('==============================================================================================\n')
    race_start.set()

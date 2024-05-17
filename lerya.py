from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class PARSER:
    def __init__(self):
        self.url = None
        self.connection = None
        self.driver = None

    def driver_connection(self):
        '''подключаем веб-драйвер, надстройки нужны чтобы обойти блокировку сайта'''
        options = Options()
        # options.add_argument("--headless") перед релизом впиши, нужно чтобы браузер не открывался
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            'source': '''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
          '''
        })

    def site_opening(self, url):
        '''открываем сайт'''
        return self.driver.get(url)

    def current_url(self):
        return self.driver.current_url

    def filling_out_forms(self, form, information):
        '''заполнение форм на сайте, используем чтобы ввести название или артикул товара'''
        try:
            return form.send_keys(information)
        except:
            return

    def click(self, click_elem):
        '''клик по элементам на сайте, например чтобы нажать кнопку поиска'''
        try:
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, click_elem))).click()
            return True
        except:
            return False

    def searching(self, elem):
        '''ищем элемент на сайте, например чтобы найти строку поиска куда мы вводим название товара'''
        try:
            result = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, elem)))
            return result
        except:
            return False


pars_page = PARSER()
pars_page.driver_connection()


def main(card_name):
    '''нужно использовать цикл чтобы например когда человек ввел товар которого нет в каталоге его не выкидывало из
    программы, а ему было предложено ввести название снова'''

    '''Здесь нужно соединить программы, name = артикул или название товара который получаем от клиента
    если мы вводим название товара открывается одно окно с поиском товара, а если артикул - другое, сразу карточка товара
    поэтому здесь нужно разделение, проверка все ли символы в строке - числа (name определен для примера)
    так как мы взаимодействуем с ссылкой нужно преобразовать введенное name человека: все пробелы нужно заменить на +'''
    card_name1 = card_name.split()
    name = '+'.join(card_name1)
    '''открываем сайт сразу с поиском по name'''
    pars_page.site_opening(f"https://novosibirsk.leroymerlin.ru/search/?q={name}&page=1")

    try:
        pars_page.click(
            '#root > div > main > div:nth-child(1) > div:nth-child(1) > div > div > div.b1jotxbu_header-footer.ctm79aj_header-footer > button')
    except:
        pass
    '''определяем что ввели: артикул или название. Наша цель - добраться до карточки товара, нас перекидывает на 
    страницу поиска, где если у нас 1 товар (например так бывает если введен артикул, то мы переходим на его 
    карточку, а если нет то отправляем боту сообщение со всеми товарами, где клиенту нужно выбрать нужный
    ниже проверка на то, введен ли артикул'''
    '''определяем количество карточек. если products_count не определено значит клиент ввел название товара
    которого нет в каталоге и попытка преобразовать products_count в число выпадет в ошибку'''
    products_count = pars_page.searching(
            '#root > div > main > div.pqgcfsa_plp > div:nth-child(2) > div > section > div.t15rxvip_plp.t1w1siz7_plp > div.phfwh3v_plp > div')
    try:
        names_count = int(products_count.text.split()[1])
    except:
        '''клиент ввел название товара которого нет в каталоге, здесь пишем боту что-то типо чел, ничего не
        нашлось, попробуй ввести другое, переопределяем и откатываемся с помощью continue в начало цикла'''
        yield False

    '''если у нас 1 товар, то идем в его карточку, если нет выводим все карточки для пользователя'''
    if names_count == 1:
        '''кликаем на его карточку'''
        pars_page.click(
                '#root > div > main > div.pqgcfsa_plp > div:nth-child(2) > div > section > div:nth-child(4) > section > div > div > a')

    else:
        '''если товаров много, нужен цикл, перед циклом напиши в бота что-то типо в каталоге по вашему запросу
        оказалось много товаров
        вложенный цикл потому что страниц с товарами несколько, внешний цикл идет по страницам, внутренний - по
        карточкам (карточек на каждой странице 30)'''
        page = 1
        '''try нам нужен, чтобы когда объявления закончились card выпал в ошибку и мы пошли дальше'''
        try:
            while True:
                for j in range(1, 31):
                    '''делаем скриншот каждой карточки товара
                    если не можем найти элемент card - значит объявления на странице закончились, идем на
                    следующую страницу'''
                    card = pars_page.searching(
                        f'#root > div > main > div.pqgcfsa_plp > div:nth-child(2) > div > section > div:nth-child(4) > section > div.pr7cfcb_plp.largeCard > div:nth-child({j})')
                    if not card:
                        break
                    '''card_image - скриншот карточки, vendor_code - ее артикул
                    я придумал, что алгорит будет такой: нам нужно вывести все карточки для пользователя,
                    чтобы он выбрал нужную, для этого мы поочередно отправляем ему скриншот карточки, а под ней
                    кнопку с ее артикулом. и так для каждой карточки (это самый оптимальный вариант, я пробовал
                    другие, но ничего не получилось)'''
                    card_image = card.screenshot_as_png
                    vendor_code = int(''.join(filter(str.isdigit, pars_page.searching(
                            f'#root > div > main > div.pqgcfsa_plp > div:nth-child(2) > div > section > div:nth-child(4) > section > div.pr7cfcb_plp.largeCard > div:nth-child({j}) > div.c1gua8e6_plp.c14mt2bm_plp.largeCard > span').text)))
                    '''выводим'''
                    yield vendor_code, card_image
                '''идем на следующую страницу с объявлениями'''
                page += 1
                url = f'https://novosibirsk.leroymerlin.ru/search/?q={name}&page={page}'
                pars_page.site_opening(url)
                current_url = pars_page.current_url()

                '''долго рассказывать как это работает, но это работает, это выход из циклов когда объявления
                полностью закончились'''
                if url[url.find('page='):] != current_url[current_url.find('page='):]:
                    raise Exception




        except (AttributeError, Exception):
            '''если мы сюда попали - объявления закончились, теперь просим пользователя нажать на кнопку с
            нужным ему товаром, берем из кнопки его артикул'''
            # bot

            '''наконец-то открываем карточку с товаром'''
    '''начинаем работать с карточкой'''
    availability = pars_page.searching(
            '#pdp-showcase > div.mocked-styled-53.p1nz4rv2_pdp > div.mocked-styled-60.s1uxecnc_pdp > div > div')
    availability_image = availability.screenshot_as_png
    yield 'no', availability_image
    time.sleep(5)

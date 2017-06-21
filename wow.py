import telebot
import conf
import flask
import requests
import json
import sys
import os
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
from datetime import datetime

TOKEN = os.environ["TOKEN2"]
#bot = telebot.TeleBot(conf.TOKEN, threaded = False)
bot = telebot.TeleBot(TOKEN, threaded=False)
bot.remove_webhook()
bot.set_webhook(url="https://astibot.herokuapp.com/bot")
app = flask.Flask(__name__)

def check_identity (identity):
    if identity.find('club') == -1 and identity.find('public') == -1:
        return identity
    else:
        temp = identity.replace('club', '')
        double_temp = temp.replace('public', '')
        identity = double_temp
        return identity
        
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Введите ссылку на сообщество. Внимание! Обработке подвергаются только сообщества с уникальным именем')

@bot.message_handler(func=lambda m: True) 
def my_function(message):
    bot.send_message(message.chat.id, 'Пожалуйста, подождите, нужно время, чтобы собрать данные')
    message_text = str(message.text)
    pos = message_text.rfind('/')
    identity = message_text[pos+1:]
    identity = check_identity(identity)
    application = 'https://api.vk.com/method/groups.getById?group_ids=' + identity 
    response = requests.get (application)
    data = json.loads (response.text)
    temp = str()
    if 'error' in data:
        bot.send_message(message.chat.id, 'К сожалению, произошла ошибка')
    else:
        if data['response'][0]['is_closed'] == 1:
            bot.send_message(message.chat.id, 'К сожалению, сообщество закрыто')
        else:
            group_id = data ['response'][0]['gid'] 
            output = open('text.txt', 'w', encoding='utf-8')
            about_city = {}
            about_age = {}
            
            def user_information (user_id):
                users_inf = 'https://api.vk.com/method/users.get?user_ids=' + str (user_id) + '&fields=city,bdate'
                response = requests.get (users_inf)
                users_inf = json.loads (response.text)
                if user_id > 0:
                    if 'city' in users_inf['response'][0]:
                        cities = users_inf['response'][0]['city']
                        if cities in about_city:
                            about_city [cities] += 1
                        else:
                            about_city [cities] = 1
                            
                    if 'bdate' in users_inf['response'][0]:
                        birth_user = users_inf['response'][0]['bdate'].split('.') 
                        date_arr = str (datetime.today()).split()[0].split('-')
                        if len (birth_user)>2:
                            age = int (date_arr[0]) - int (birth_user[2])
                            if age in about_age:
                                about_age [age] += 1
                            else:
                                about_age [age] = 1
                        
                            
            to_begin = 'https://api.vk.com/method/wall.get?owner_id=-'+ str (group_id) + '&count=10' + '&access_token=3a5917933a5917933a591793f03a05db6833a593a59179363113890d156321fe2b84498'
            response_wall = requests.get (to_begin)
            data_wall = json.loads (response_wall.text)
            for j in range (10):
                print(data_wall['response'][j+1]['text'].translate(non_bmp_map), file = output)
                post_id = data_wall['response'][j+1]['id']
                comments_wall = 'https://api.vk.com/method/wall.getComments?owner_id=-'+ str (group_id) + '&post_id=' + str (post_id) + '&count=100'#+'&offset='+ str(100*i) 
                response_comments_wall = requests.get (comments_wall)
                data_comments_wall = json.loads (response_comments_wall.text)
                for m in range (1,len (data_comments_wall['response'])):
                    print(data_comments_wall['response'][m]['text'].translate(non_bmp_map), file = output)
            output.close()
            
            group_info = 'https://api.vk.com/method/groups.getMembers?group_id='+ str (group_id) + '&count=220' + '&access_token=3a5917933a5917933a591793f03a05db6833a593a59179363113890d156321fe2b84498'        
            response_group = requests.get (group_info)
            data_user = json.loads (response_group.text)
            
            for j in range(len(data_user['response']['users'])):
                user_information(data_user['response']['users'][j])
            
            reply = str()
            reply += 'Всего пользователей сообщества: \n'
            reply += str(data_user['response']['count']) + '\n\n'
            reply += 'Топ10 городов сообщества:\n'
            top10_cities = sorted(about_city.items(), key=lambda item:item[1])
            make_str = str()
            for key in top10_cities:
                make_str += str(key[0]) + ','
                
            convert = 'https://api.vk.com/method/database.getCitiesById?city_ids=' + make_str[:len(make_str)-1] + '&access_token=3a5917933a5917933a591793f03a05db6833a593a59179363113890d156321fe2b84498'
            response_city = requests.get(convert)
            data_city = json.loads (response_city.text)
            
            for i in range(10):
                if len(data_city['response']) > i:
                    reply += str(i+1) + ' место: ' + data_city['response'][len(data_city['response']) - i - 1]['name'] + '\n'
            
            reply += '\nСредний возраст пользователей сообщества:\n'
            average = round(sum([key*value for key,value in about_age.items()])/sum(about_age.values()),2)
            reply += str(average) + '\n\n'
            reply += '10 последних ключевых слов:\n'
            from rutermextract import TermExtractor
            
            key_text = open('text.txt', 'r', encoding='utf-8').read()
            ex = TermExtractor()
            top_10 = 10
            counter = 0
            for term in ex(key_text):
                if counter < top_10:
                    counter += 1
                    if term.normalized != '<br>':
                        reply += str(counter) + ' место: ' + term.normalized + '\n'
                    else: 
                        counter -= 1
            bot.send_message(message.chat.id, reply)

@app.route("/", methods=['GET', 'HEAD'])
def index():
    return 'ok'

# страница для нашего бота
@app.route("/bot", methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
    
if __name__ == '__main__':
    import os
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

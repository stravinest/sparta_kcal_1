from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import math
import requests
import jwt
import hashlib
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'


# client = MongoClient('localhost', 27017)
# db = client.todayKcal


client = MongoClient('15.164.218.10', 27017, username="test", password="test")
db = client.dbsparta_1stminiproject


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        #user_info가 index에 넘어감
        return render_template('index.html', user_info=payload["id"])

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


# 로그인 페이지
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


## API 역할을 하는 부분

# [로그인 API]
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 회원가입페이지
@app.route('/member/join')
def member_join():
    return render_template("join.html")

@app.route('/member/check', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

@app.route('/member/checknickname', methods=['POST'])
def check_nick():
    nickname_receive = request.form['nickname_give']
    exists = bool(db.users.find_one({"nickname": nickname_receive}))
    return jsonify({'result': 'success', 'exists': exists})

@app.route('/mamber/join', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    nickname_receive = request.form['nickname_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    exists = bool(db.users.find_one({"username": username_receive}))
    if exists:
        return jsonify({'result': 'success', 'exists': exists});

    exists_nick = bool(db.users.find_one({"nickname": nickname_receive}))
    if exists_nick:
        return jsonify({'result': 'success', 'exists_nick': exists_nick})

    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "nickname": nickname_receive,                               # 닉네임
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


#음식정보 입력
@app.route('/index', methods=['POST'])
def write_review():
    token_receive = request.cookies.get('mytoken')  # 쿠키를 항상 가져 옴
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})  # 유저 정보를 항상 알 수 있음

        foodName_receive = request.form['foodName_give']
        foodDate_receive = request.form['foodDate_give']
        foodKcal_receive = request.form['foodKcal_give']
        now_receive = request.form['now_give']
        userinfo_receive = request.form['userinfo_give']
        mainUser_receive = request.form['main_user']
        print(userinfo_receive)

        file = request.files["file_give"]

        extension = file.filename.split('.')[-1]
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

        today =int(today.strftime(('%Y%m%d')))

        print(today)

        filename = f'file-{mytime}'
        save_to = f'static/img/{filename}.{extension}'
        file.save(save_to)

        doc = {
            'user_info': userinfo_receive,
            'food_name': foodName_receive,
            'user_nick': mainUser_receive,
            'food_date': foodDate_receive,
            'food_kcal': int(foodKcal_receive),
            'file': f'{filename}.{extension}',
            'now': now_receive,
            'today': int(today)
        }

        db.foodInfo.insert_one(doc)

        return jsonify({'msg': '저장 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))



#음식정보 받기

@app.route('/index', methods=['GET'])
def show_diary():
    user_info_receive = request.args.get("user_info")
    foodInfos = list(db.foodInfo.find({}, {'_id': False}).sort("now", -1))
    user_nick = list(db.users.find({}, {'_id': False}))

    return jsonify({'all_foods': foodInfos, 'user': user_nick})


# 오늘의 프로필로 보내기
@app.route('/api/send', methods=['GET'])
def send():
    try:
        token_receive = request.cookies.get('mytoken')
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload['id'])
        profiles = list(db.todayKcal.find({"myid": payload['id']}, {'_id': False}))
        if (profiles == []):
            status = 'new'
        else:
             status = 'old'
        print(status)
        return jsonify({'status': status})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))



# 오늘의프로필 페이지
@app.route('/profile')
def profile():
    token_receive = request.cookies.get('mytoken')
    try:
        status_receive = request.args.get("status_give")
        print(status_receive)
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload['id'])
        return render_template("profile.html", status=status_receive, userid=payload['id'])

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

# 오늘의프로필등록
@app.route('/api/profile_post', methods=['POST'])
def save_profile():
    myid_receive = request.form['myid_give']
    height_receive = request.form['heigt_give']
    weight_receive = request.form['weight_give']
    goal_cal_receive = request.form['goal_cal_give']
    h = int(height_receive)
    w = int(weight_receive)
    bmiscore = math.trunc(w / (h * h) * 10000)
    bmi = ""
    if (bmiscore > 30):
        bmi = "비만"
    elif (bmiscore >= 25):
        bmi = "과체중"
    elif (bmiscore >= 19):
        bmi = "정상"
    else:
        bmi = "저체중"


    doc = {
        'myid': myid_receive,
        'height': int(height_receive),
        'weight': int(weight_receive),
        'goal_cal': int(goal_cal_receive),
        'bmi': bmi,
        'bmiscore': int(bmiscore)
    }
    db.todayKcal.insert_one(doc)

    return jsonify({'msg': '등록 완료!'})


# 오늘의 프로필 리스팅
@app.route('/api/profile', methods=['GET'])
def show_profile():
    status_receive = request.args.get("status_give")
    myid_receive = request.args.get("myid")
    # print(status_receive)
    profiles = list(db.todayKcal.find({"myid": myid_receive}, {'_id': False}))
    if (profiles == []):
        status = 'new'
    else:
        status = 'old'
    # print(status)
    return jsonify({'profiles': profiles, 'status': status})


# 프로필 칼로리계산
@app.route('/api/profile_cal', methods=['GET'])
def show_profile_cal():
    myid_receive = request.args.get("myid")
    print(myid_receive)

    agg_result = db.foodInfo.aggregate(
        [
            {
                "$match": {'user_info': myid_receive}
            },
            {
                "$group":
                    {
                        "_id": {"user_id": "$user_info",
                                "date": "$food_date",

                                },

                        "total": {"$sum": "$food_kcal"},
                        "avg": {"$avg": "$today"}

                    }},
            {
                "$sort": {"avg": -1}
            },

            {
                "$limit": 3
            },

        ])

    date_kalsum = list(agg_result)

    foodInfos = list(db.foodInfo.find({"user_info": myid_receive}, {'_id': False}))
    goal_cal = list(db.todayKcal.find({"myid": myid_receive}, {'_id': False}).sort("now", -1))

    return jsonify({'all_foods': foodInfos, 'date_kalsum': date_kalsum, 'goal_cal': goal_cal})


# 오늘의 프로필 수정
@app.route('/api/profile_adjust', methods=['POST'])
def update_profile():
    myid_receive = request.form['myid_give']
    height_receive = request.form['heigt_give']
    weight_receive = request.form['weight_give']
    goal_cal_receive = request.form['goal_cal_give']
    h = int(height_receive)
    w = int(weight_receive)
    bmiscore = math.trunc(w / (h * h) * 10000)
    bmi = ""
    if (bmiscore > 30):
        bmi = "비만"
    elif (bmiscore >= 25):
        bmi = "과체중"
    elif (bmiscore >= 19):
        bmi = "정상"
    else:
        bmi = "저체중"

    print(myid_receive)
    print(height_receive)

    db.todayKcal.update_one({'myid': myid_receive}, {'$set': {'height': int(height_receive)}})
    db.todayKcal.update_one({'myid': myid_receive}, {'$set': {'weight': int(weight_receive)}})
    db.todayKcal.update_one({'myid': myid_receive}, {'$set': {'goal_cal': int(goal_cal_receive)}})
    db.todayKcal.update_one({'myid': myid_receive}, {'$set': {'bmi': bmi}})
    db.todayKcal.update_one({'myid': myid_receive}, {'$set': {'bmiscore': int(bmiscore)}})

    return jsonify({'result': 'success'})

#프로필 음식 사진출력
@app.route('/api/profile_food', methods=['GET'])
def show_food_cal():
    myid_receive = request.args.get("myid")
    print(myid_receive)

    foodInfos = list(db.foodInfo.find({"user_info":myid_receive}, {'_id': False}).sort("now", -1))

    print(foodInfos)
    return jsonify({'all_foods': foodInfos})

@app.route('/api/profile_delete', methods=['POST'])
def delete_profile():
    filename_receive = request.form['filename_give']
    print(filename_receive)
    result = db.foodInfo.delete_one({'file': filename_receive})
    print(result)
    return jsonify({'result': 'success'})


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
#오류 뜸

if __name__ == '__main__':

    app.run('0.0.0.0', port=5000, debug=True)
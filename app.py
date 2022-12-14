import imp
from flask import Flask,session,flash,render_template,request,redirect,url_for,send_file
from flask_bootstrap import Bootstrap
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import tempfile 
import moviepy.editor as mp
import shutil
import youtube_dl
import glob
import gc
import cv2
import ffmpeg

UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'mpg'}

app=Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1000 * 1000 * 1000
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///situation.db'
db=SQLAlchemy(app)
bootstrap=Bootstrap(app)

app.secret_key='9KStWezC'

class Post(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    brand1_case1=db.Column(db.String(50),nullable=False)
    brand2_case1=db.Column(db.String(50),nullable=False)
    brand3_case1=db.Column(db.String(50),nullable=False)
    brand1_case2=db.Column(db.String(50),nullable=False)
    brand2_case2=db.Column(db.String(50),nullable=False)
    brand3_case2=db.Column(db.String(50),nullable=False)
    p1_case1=db.Column(db.String(50),nullable=False)
    p2_case1=db.Column(db.String(50),nullable=False)
    p3_case1=db.Column(db.String(50),nullable=False)
    p1_case2=db.Column(db.String(50),nullable=False)
    p2_case2=db.Column(db.String(50),nullable=False)
    p3_case2=db.Column(db.String(50),nullable=False)
    start_sim_invest=db.Column(db.String(50),nullable=False)
    end_sim_invest=db.Column(db.String(50),nullable=False)
    start_sim_dissaving=db.Column(db.String(50),nullable=False)
    method_case1=db.Column(db.String(50),nullable=False)
    method_case2=db.Column(db.String(50),nullable=False)
    r_case1=db.Column(db.String(50),nullable=False)
    r_case2=db.Column(db.String(50),nullable=False)

@app.route('/',methods=['GET','POST'])
def index():
    if request.method=='GET':
        if "outgo" in session:
            outgo=session["outgo"]
        return render_template('index.html')

    if request.method=='POST':
        brand = request.form.getlist("brand")
        p = request.form.getlist("p")
        sim=request.form.get("sim")
        value0_b = request.form.get("value0_b")
        cash0_b = request.form.get("cash0_b")
        saving = request.form.get("saving")
        income=[100]*30
        if "income" in session:
            income = session["income"]
        goal = request.form.get("goal")

        value0_a = request.form.get("value0_a")
        cash0_a = request.form.get("cash0_a")
        method = request.form.getlist("method")
        r = request.form.getlist("r")
        outgo=[100]*30
        if "outgo" in session:
            outgo=session["outgo"]
        
        session['brand']=brand
        session['p']=p
        session['sim']=sim
        session['value0_b']=value0_b
        session['cash0_b']=cash0_b
        session['saving']=saving
        session['goal']=goal

        session['value0_a']=value0_a
        session['cash0_a']=cash0_a
        session['method']=method
        session['r']=r

        import datetime as dt
        import analysis as an

        start = dt.date(year=1920,month=1,day=1)
        end = dt.datetime.now().date()
        periods=[1,5,10,15,20,25,30]
        lst_case1=[[brand[0],float(p[0])],[brand[2],float(p[2])],[brand[4],float(p[4])]]
        df_case1=an.portfolio(lst_case1,start,end)
        interest_case1=an.interest(df_case1.copy(),periods)

        lst_case2=[[brand[1],float(p[1])],[brand[3],float(p[3])],[brand[5],float(p[5])]]
        df_case2=an.portfolio(lst_case2,start,end)
        interest_case2=an.interest(df_case2.copy(),periods)

        fig=an.fig_chart(df_case1.copy(),df_case2.copy())
        fig.write_html("templates/fig1.html")
        fig=an.fig_interest(interest_case1,interest_case2)
        fig.write_html("templates/fig2.html")
        fig=an.fig_interest_dispersion(periods,interest_case1,interest_case2)
        fig.write_html("templates/fig3.html")
        fig=an.fig_total_interest_dispersion(periods,interest_case1,interest_case2)
        fig.write_html("templates/fig4.html")
        page='portfolio'

        # FIRE???????????????????????????????????????
        if sim=='before':
            
            for i in range(len(income)):
                income[i] = int(income[i])
            df_goal1,df_goal1_all=an.sim_goal(df_case1.copy(),int(saving),int(value0_b),int(cash0_b),income,int(goal))
            df_goal2,df_goal2_all=an.sim_goal(df_case2.copy(),int(saving),int(value0_b),int(cash0_b),income,int(goal))

            success_goal1=an.sim_dissaving_dash(df_goal1_all.copy())
            success_goal2=an.sim_dissaving_dash(df_goal2_all.copy())


            fig=an.fig_fire_success_dash(success_goal1.copy(),success_goal2.copy())
            fig.write_html("templates/fig21.html")
            fig=an.fig_sim_dispersion_dash(df_goal1_all.copy(),df_goal2_all.copy())
            fig.write_html("templates/fig22.html")
            fig=an.fig_sim_dash(*df_goal1_all.copy())
            fig.write_html("templates/fig23.html")
            fig=an.fig_sim_goal(df_goal1[0].copy())
            fig.write_html("templates/fig24.html")
            fig=an.fig_sim_goal(df_goal1[1].copy())
            fig.write_html("templates/fig25.html")      
            fig=an.fig_sim_goal(df_goal1[2].copy())
            fig.write_html("templates/fig26.html")

            page='simulation1'


        # FIRE????????????????????????????????????
        if sim=='after':
            sim_dissaving_case1,success_dissaving_case1=an.sim_dissaving(df_case1.copy(),start,float(r[0])/100,int(method[0]))

            sim_dissaving_case2,success_dissaving_case2=an.sim_dissaving(df_case2.copy(),start,float(r[1])/100,int(method[1]))

            for i in range(len(outgo)):
                outgo[i] = int(outgo[i])
            df_fire1,df_fire1_all=an.sim_fire(df_case1.copy(),float(r[0])/100,int(method[0]),int(value0_a),int(cash0_a),outgo)
            df_fire2,df_fire2_all=an.sim_fire(df_case2.copy(),float(r[1])/100,int(method[1]),int(value0_a),int(cash0_a),outgo)

            success_fire1=an.sim_dissaving_dash2(df_fire1_all.copy())
            success_fire2=an.sim_dissaving_dash2(df_fire2_all.copy())


            fig=an.fig_fire_success_dash(success_fire1.copy(),success_fire2.copy())
            fig.write_html("templates/fig1.html")
            fig=an.fig_sim_dispersion_dash(df_fire1_all.copy(),df_fire2_all.copy())
            fig.write_html("templates/fig2.html")
            fig=an.fig_sim_dash(*df_fire1_all.copy())
            fig.write_html("templates/fig3.html")
            fig=an.fig_sim_fire(df_fire1[0].copy())
            fig.write_html("templates/fig4.html")
            fig=an.fig_sim_fire(df_fire1[1].copy())
            fig.write_html("templates/fig5.html")      
            fig=an.fig_sim_fire(df_fire1[2].copy())
            fig.write_html("templates/fig6.html")

            page='simulation2'

        return redirect(f'/{page}')

@app.route('/fig/<i>',methods=['GET','POST'])
def fig(i):
    return render_template(f'fig{i}.html')

@app.route('/portfolio',methods=['GET'])
def portfolio():

    if request.method=='GET':
        brand=session['brand']
        brand_jp=['undefined']*len(brand)
        for i in range(len(brand)):
            if brand[i]=='^DJI':
                brand_jp[i] = '??????????????????'
            if brand[i]=='^SPX':
                brand_jp[i] = 'S&P 500'
            if brand[i]=='^NDQ':
                brand_jp[i] = 'NASDAQ'
            if brand[i]=='10USYB':
                brand_jp[i] = '???10??????'
        session['brand_jp']=brand_jp

        return render_template('portfolio.html')

@app.route('/simulation1',methods=['GET','POST'])
def simulation1():
    if request.method=='GET':
        brand=session['brand']
        brand_jp=['undefined']*len(brand)
        for i in range(len(brand)):
            if brand[i]=='^DJI':
                brand_jp[i] = '??????????????????'
            if brand[i]=='^SPX':
                brand_jp[i] = 'S&P 500'
            if brand[i]=='^NDQ':
                brand_jp[i] = 'NASDAQ'
            if brand[i]=='10USYB':
                brand_jp[i] = '???10??????'
        session['brand_jp']=brand_jp

        return render_template('simulation1.html')

@app.route('/simulation2',methods=['GET','POST'])
def simulation2():
    if request.method=='GET':
        brand=session['brand']
        brand_jp=['undefined']*len(brand)
        for i in range(len(brand)):
            if brand[i]=='^DJI':
                brand_jp[i] = '??????????????????'
            if brand[i]=='^SPX':
                brand_jp[i] = 'S&P 500'
            if brand[i]=='^NDQ':
                brand_jp[i] = 'NASDAQ'
            if brand[i]=='10USYB':
                brand_jp[i] = '???10??????'
        session['brand_jp']=brand_jp

        method=session['method']
        method_jp=['undefined']*len(method)
        for i in range(len(method)):
            if method[i]=='0':
                method_jp[i] = '??????'
            if method[i]=='1':
                method_jp[i] = '??????'
        session['method_jp']=method_jp

        return render_template('simulation2.html')
    
@app.route('/income',methods=['GET','POST'])
def income():
    if request.method=='POST':
        income = request.form.getlist("income")
        session['income']=income
        return redirect('/')
    else:
        return render_template('income.html')

@app.route('/outgo',methods=['GET','POST'])
def outgo():
    if request.method=='POST':
        outgo = request.form.getlist("outgo")
        session['outgo']=outgo
        return redirect('/')
    else:
        return render_template('outgo.html')

@app.route('/reference',methods=['GET'])
def reference():
    import datetime as dt
    import analysis as an

    # ????????????
    brand1='^DJI'
    brand2='^SPX'
    brand3='^NDQ'

    # ??????????????????
    start = dt.date(year=1920,month=1,day=1)
    end = dt.datetime.now().date()
    
    df1=an.stock(brand1,start,end)
    df2=an.stock(brand2,start,end)
    df3=an.stock(brand3,start,end)
    df_gdp=an.stock('GDP',start,end)

    fig=an.fig_gdp(df1.copy(),df_gdp.copy())
    fig.write_html("templates/fig101.html")
    fig=an.fig_gdp(df2.copy(),df_gdp.copy())
    fig.write_html("templates/fig102.html")
    fig=an.fig_gdp(df3.copy(),df_gdp.copy())
    fig.write_html("templates/fig103.html")

    return render_template('reference.html')




# ???????????????????????????
import requests

@app.route('/editor',methods=['GET','POST'])
def editor():
    if request.method=='POST':
        # ??????????????????????????????
        video = request.files['video']
        # ??????????????????????????????
        music = request.files['music']
        # ????????????YouTube???URL???????????????????????????????????????
        url = request.form.get("youtube")  

        # ?????????????????????????????????????????????????????????
        tmpdir = tempfile.mkdtemp()
        VIDEOS_DIR = tmpdir+'/data/video/'
        MUSIC_DIR = tmpdir+'/data/music/'
        TARGET_IMAGES_DIR = tmpdir+'/data/images/target/'
        os.makedirs(VIDEOS_DIR)
        os.makedirs(MUSIC_DIR)
        os.makedirs(TARGET_IMAGES_DIR)

        # ???????????????????????????
        video_name = secure_filename(video.filename)
        video_path=os.path.join(VIDEOS_DIR, video_name)
        video.save(video_path)

        # ????????????????????????????????????YouTube????????????????????????????????????????????????
        if music.filename == '':
            data = {
                "url": url,
            }
            r = requests.post(
                "https://detector-app-20221031-3-5-d6ljr4zrfa-an.a.run.app/classification",
                json=data,
            )
            music_name = "ytmusic.mp3"
        # ?????????????????????????????????
        else:
            music_name = secure_filename(music.filename)
            music_path=os.path.join(MUSIC_DIR, music_name)
            #music.save(music_path)
            music.save("./uploads/music/"+music_name)


        # ????????????????????????????????????????????????
        sampling_sec = 5
        # ????????????????????????????????????????????????
        frame_path = TARGET_IMAGES_DIR
        # ??????????????????????????????????????????
        video = cv2.VideoCapture(video_path)
        fps = int(sampling_sec * video.get(cv2.CAP_PROP_FPS))
        i = 0
        while video.isOpened():
            ret, frame = video.read()
            if ret == False:
                break
            if i % fps == 0:
                # path?????????????????????????????????
                #cv2.imwrite(frame_path + "img_%s.png" % str(i).zfill(6), frame)
                cv2.imwrite("./uploads/frames/" + "img_%s.png" % str(i).zfill(6), frame)
            i += 1
        video.release()

        # ????????????????????????????????????????????????????????????????????????????????????
        scene = selecting_scene(frame_path)

        # ?????????????????????
        video = cv2.VideoCapture(video_path)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        size = (width, height)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_rate = int(video.get(cv2.CAP_PROP_FPS))
        fmt = cv2.VideoWriter_fourcc("m", "p", "4", "v")

        # ????????????????????????
        Ts = 25
        scene2 = [0]
        for i in range(len(scene) - 1):
            if scene[i] * sampling_sec + Ts / 2 < scene[i + 1] * sampling_sec - Ts / 2:
                scene2.append(scene[i + 1])

        new_video_sec = (len(scene2) - 1 / 2) * Ts
        music_sec = 100

        # ???????????????????????????????????????????????????????????????
        x = 1
        if new_video_sec > music_sec:
            x = int(new_video_sec / music_sec)
        elif new_video_sec <= music_sec:
            music_sec = new_video_sec
        # ??????????????????????????????
        new_video_name=video_name.rsplit('.', 1)[0]+'_edited.mp4'
        cutout_path = app.config['UPLOAD_FOLDER']+'driving/'+new_video_name
        writer = cv2.VideoWriter(cutout_path, fmt, x * frame_rate, size)

        # ??????????????????????????????????????????
        for s in scene2:
            start = s * sampling_sec - Ts / 2
            if start < 0:
                start = 0

            end = s * sampling_sec + Ts / 2
            if end > frame_count * frame_rate:
                end = frame_count * frame_rate

            i = start * frame_rate
            video.set(cv2.CAP_PROP_POS_FRAMES, i)
            while i <= end * frame_rate:
                ret, frame = video.read()
                writer.write(frame)
                i = i + 1

        writer.release()
        video.release()
        cv2.destroyAllWindows()

        # ????????????????????????
        video_path="http://iut-b.main.jp/uploads/driving/"+new_video_name
        music_path="http://iut-b.main.jp/uploads/music/"+music_name
        data = {
            "video_path": video_path,
            "music_path": music_path,
            "new_video_path": new_video_name,
        }
        r = requests.post(
            "https://detector-app-20221031-2-15-d6ljr4zrfa-an.a.run.app/classification",
            json=data,
        )

        # ???????????????????????????????????????????????????????????????????????????
        session['new_video_name']=new_video_name


        gc.collect()
        shutil.rmtree(tmpdir)

        return redirect('/driving_finished')
        #return url

    else:
        return render_template('index2.html')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def selecting_scene(frame_path):
    # ?????????????????????????????????
    images = [f for f in os.listdir("./uploads/frames") if f[-4:] in [".png", ".jpg"]]
    data = {
        "url": "http://iut-b.main.jp/uploads/frames/",
        "images": images,
        "Nc": 3,
    }
    r = requests.post(
        "https://detector-app-20221031-14-d6ljr4zrfa-an.a.run.app/classification",
        json=data,
    )
    d = r.json()
    scene = d["scene"]

    return scene

# ???????????????????????????????????????????????????
@app.route('/driving_finished',methods=['GET','POST'])
def driving_finished():
    if request.method=='POST':
        name = session['new_video_name']
        return send_file(app.config['UPLOAD_FOLDER']+name, as_attachment=True,mimetype='video/mp4')
    else:
        return render_template('driving_finished.html')

# ???????????????????????????????????????????????????
@app.route('/up',methods=['GET','POST'])
def up():
    if request.method=='POST':
        upload_file = request.files['file']
        upload_file.save('./uploads/'+upload_file.filename)
        return render_template('index2.html')
    else:
        return render_template('driving_finished.html')

# ????????????YouTube???????????????????????????????????????
@app.route('/up2',methods=['GET','POST'])
def up2():
    if request.method=='POST':
        upload_file = request.files['file']
        upload_file.save('./uploads/music/'+upload_file.filename)
        return render_template('index2.html')
    else:
        return render_template('driving_finished.html')

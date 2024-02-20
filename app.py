# coding=utf-8
import os
from flask import Flask, flash, request, redirect, url_for, render_template, current_app
from werkzeug.utils import secure_filename
from flask import send_from_directory
import random, time
import db
import getConfig as gcf
import json
from flask import jsonify 
from flask.cli import with_appcontext
from datetime import datetime

cf = gcf.get_config()

allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
upload_folder = os.path.join(os.getcwd(), 'pics')
print(upload_folder)
app = Flask(__name__, instance_relative_config=True)

def print_json(file_data):
 print(json.dumps(file_data, sort_keys=True, indent=4, separators=(', ', ': '), ensure_ascii=False))

@app.route('/local_pic_host', methods=['POST','GET'] )
def local_picuse_host():
    if request.method == 'POST':
       # 检查post请求中是否有文件
        if 'file' not in request.files:
            flash('你没有上传文件！')
            return redirect(request.url)
        file = request.files['file']
        print(file)
        file_link = ''
        if file.filename == '':
            flash('你没有选择文件！')
            return redirect(request.url)
        if file and allowed_file(file.filename):           
            filename = str(file.filename)#配合quicker动作使用，不重命名了，如果需要可以参考下面原始方法的重命名
            try:
                file.save(os.path.join(upload_folder, filename))#
                database = db.get_db()
                database.execute(
                    'INSERT INTO pics (filename)'
                    ' VALUES (?)',
                    (filename,)
                )
                database.commit()
                if app.config['running_port'] != 80:
                    file_link = request.host.split(':')[0] + ':' + str(app.config['running_port']) + url_for('uploaded_file', filename=filename) #不是80的时候改成对应端口比如加上:8888
                    flash(file_link)
                else:
                    file_link = request.host.split(':')[0] + url_for('uploaded_file', filename=filename)
                    flash(file_link)
            except Exception as e:
                flash('出现错误！')
                print(e.args)
            print({'file_data':'http://'+file_link})#输出链接，方便直接点开
            print_json(json.dumps({'file_data':'http://'+file_link},ensure_ascii=False))#输出json调试信息
            return json.dumps({'file_data':'http://'+file_link},ensure_ascii=False)#给picgo插件api接口返回
        else:
            flash('不被服务器支持的文件！')
            return redirect(url_for('upload_file'))
    database = db.get_db()
    pcnum = database.execute("SELECT Count(*) FROM pics").fetchone()[0]
    print(pcnum)
    print(json.dumps({'file_data':file_link}))
    return json.dumps({'file_data':'http://'+file_link},ensure_ascii=False)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/', methods=['POST', 'GET'] )
def upload_file():
    if request.method == 'POST':
        # 检查post请求中是否有文件
        if 'file' not in request.files:
            flash('你没有上传文件！')
            return redirect(request.url)
        file = request.files['file']
        print(file)
        if file.filename == '':
            flash('你没有选择文件！')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = str(int(time.time())) + str(random.randint(1, 99999)) + secure_filename(str(random.randint(1, 7887)) + file.filename)
            try:
                file.save(os.path.join(upload_folder, filename))
                database = db.get_db()
                database.execute(
                    'INSERT INTO pics (filename)'
                    ' VALUES (?)',
                    (filename,)
                )
                database.commit()
                if app.config['running_port'] != 80:
                    flash(app.config['running_domain'] + ':' + str(app.config['running_port']) + url_for('uploaded_file', filename=filename))
                else:
                    flash(app.config['running_domain'] + url_for('uploaded_file', filename=filename))
            except Exception as e:
                flash('出现错误！')
                print(e.args)

            return redirect(url_for('upload_file'))
        else:
            flash('不被服务器支持的文件！')
            return redirect(url_for('upload_file'))
    database = db.get_db()
    pcnum = database.execute("SELECT Count(*) FROM pics").fetchone()[0]
    print(pcnum)

    return render_template('bs_index.html', pic_num=pcnum)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/query', methods=['GET'])
def query_images():
    image_list = []
    for filename in os.listdir(upload_folder):
        if allowed_file(filename):
            file_path = url_for('uploaded_file', filename=filename)
            image_list.append({'filename': filename, 'file_path': file_path, 'upload_time': datetime.fromtimestamp(os.path.getctime(os.path.join(upload_folder, filename))).strftime('%Y-%m-%d %H:%M')})

    # 按照上传时间倒序排序
    image_list.sort(key=lambda x: x['upload_time'], reverse=True)
    return render_template('image_list.html', image_list=image_list)



if __name__ == '__main__':

    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['running_domain'] = cf['running_domain']
    app.config['running_port'] = cf['port']
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * int(cf['max_length'])
    app.config.from_mapping(
        SECRET_KEY='dgvbv43@$ewedc',
        DATABASE=os.path.join(app.instance_path, 'my-easy-pic-bed.sqlite'),
    )
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    try:
        os.mkdir(upload_folder)
    except Exception as e:
        pass

    app.run(debug=False, host=app.config['running_domain'], port=app.config['running_port'])




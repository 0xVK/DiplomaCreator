import os
from docxtpl import DocxTemplate
import xmltodict
import datetime
import shutil
from flask import Flask, request, render_template, send_file, redirect, make_response
import config

app = Flask(__name__, template_folder='web', static_folder='web', static_url_path='/static')


def create_diploma_for_user(group_folder, user=None, diploma_type=None):

    if user is None:
        user = {}

    # SexID 1 boy, 2 girl
    end_str = 'закінчила у {} році' if user.get('SexId') == '2' else 'закінчив у {} році'

    year_of_issue_date = datetime.datetime.strptime(user.get('IssueDate'), '%d.%m.%Y %H:%M:%S').year
    user['zakinchyv'] = end_str.format(year_of_issue_date)

    user['zdobuv'] = 'здобула' if user.get('SexId') == '2' else 'здобув'

    user['vidznaka'] = user.get('AwardTypeId') == '3'

    user_doc_name = '_Відзнака - {} {}.docx' if user['vidznaka'] else '{} {}.docx'

    user_doc_name = user_doc_name.format(user.get('LastName'), user.get('FirstName'))

    doc = DocxTemplate(config.diploma_types.get(diploma_type))

    doc.render(user)

    doc.save(os.path.join(group_folder, user_doc_name))


def read_users_data_from_xml(filename):

    # Відкриваємо XML файл і створємо список
    with open(filename, 'r') as xml_file:
        xml_data = xmltodict.parse(xml_file.read())

    # Дані про всіх студентів групи
    users = xml_data.get('Documents', {}).get('Document', [])

    if isinstance(users, list):
        return users
    else:
        tmp = list()
        tmp.append(users)
        return tmp


def fill_group_data(user=None, dip_type=''):

    user_data = dict(user)
    group_data = dict()

    if dip_type in ('type-5', 'type-6'):
        stupin = dict(ua='магістр', en='Master\'s')
    else:
        stupin = dict(ua='бакалавр', en='Bachelor\'s')

    # Ua info
    # Рік закінчення
    group_data['IssueYear'] = datetime.datetime.strptime(user_data.get('IssueDate'), '%d.%m.%Y %H:%M:%S').year
    # Назва університету
    group_data['UniversityName'] = user_data.get('UniversityName')
    # Освітня програма
    group_data['StudyProgramName'] = user_data.get('StudyProgramName')
    # Професійна кваліфікація
    group_data['QualificationName'] = user_data.get('QualificationName')
    # Ступінь вищої освіти
    group_data['Stupin'] = stupin.get('ua')
    # Спеціальність
    study_group_name = user_data.get('StudyGroupName', '')
    if '.' in study_group_name:
        study_group_name = study_group_name.split('.')[0]
    group_data['SpecialityName'] = study_group_name + ' ' + user_data.get('SpecialityName', '')
    # Спеціалізація
    if dip_type in ('type-2',):
        group_data['SpecializationName'] = user_data.get('SpecializationName', '')
    else:
        group_data['SpecializationName'] = user_data.get('SpecialityName', '') + ' ' + \
                                           '(' + user_data.get('SpecializationName', '') + ')'
    # Посада головного(ної)
    group_data['BossPost'] = user_data.get('BossPost')
    # Прізвище та ініціали
    group_data['BossFIO'] = user_data.get('BossFIO')
    # Напрям підготовки
    group_data['NapramPidg'] = user_data.get('StudyGroupName', '') + ' ' + \
                               user_data.get('SpecialityName', '')

    # 31.12.2018 0:00:00
    datetime_object = datetime.datetime.strptime(user_data.get('GraduateDate'), '%d.%m.%Y %H:%M:%S')

    group_data['GraduateDateStr'] = '{} {} / {} {} р.'.format(datetime_object.day,
                                                              config.month.get(datetime_object.month),
                                                              config.month_en.get(datetime_object.month),
                                                              datetime_object.year)

    # En info
    # Назва університету
    group_data['UniversityNameEn'] = user_data.get('UniversityNameEn')
    # Освітня програма
    group_data['StudyProgramNameEn'] = user_data.get('StudyProgramNameEn')
    # Професійна кваліфікація
    group_data['QualificationNameEn'] = user_data.get('QualificationNameEn')
    # Ступінь вищої освіти
    group_data['StupinEn'] = stupin.get('en')
    # Спеціальність
    study_group_name = user_data.get('StudyGroupName', '')
    if '.' in study_group_name:
        study_group_name = study_group_name.split('.')[0]
    group_data['SpecialityNameEn'] = study_group_name + ' ' + user_data.get('SpecialityNameEn', '')
    # Спеціалізація
    if dip_type in ('type-2',):
        group_data['SpecializationNameEn'] = user_data.get('SpecializationNameEn', '')
    else:
        group_data['SpecializationNameEn'] = user_data.get('StudyGroupName', '') + ' ' + \
                                              user_data.get('SpecialityNameEn', '') + ' ' + \
                                              '(' + user_data.get('SpecializationNameEn', '') + ')'
    # Посада головного(ної)
    group_data['BossPostEn'] = user_data.get('BossPostEn')
    # Прізвище та ініціали
    group_data['BossFIOEn'] = user_data.get('BossFIOEn')
    # Напрям підготовки
    group_data['NapramPidgEn'] = user_data.get('StudyGroupName', '') + ' ' + \
                                 user_data.get('SpecialityNameEn', '')

    return group_data


@app.route('/')
def index():

    dip_type = request.cookies.get('dip-type')

    return render_template('index.html', data=dict(dip_type=dip_type))


@app.route('/archive')
def archive():

    return render_template('archive.html', files=os.listdir('generated'))


@app.route('/check', methods=["POST", "GET"])
def check():

    if request.method != 'POST':
        return 'Bad request type. '

    xml_file = request.files.get('xml-file')

    if not xml_file:
        return 'Bad XML file'

    filename = os.path.join('tmp', xml_file.filename)
    xml_file.save(filename)

    # Дані про всіх студентів групи
    users = read_users_data_from_xml(filename)
    study_group_name = users[0].get('StudyGroupName', 'невідома група')

    awards_count = 0

    for user in users:
        if user.get('AwardTypeId') == '3':
            awards_count += 1

    # Передаємо дані першого студента
    group_data = fill_group_data(user=users[0], dip_type=request.form.get('dip-type'))

    data = {
        'users_count': len(users),
        'awards_count': awards_count,
        'group_data': group_data,
        'file_name': filename,
        'dip_type': request.form.get('dip-type'),
        'study_group_name': study_group_name,
    }

    resp = make_response(render_template('check.html', data=data))
    resp.set_cookie('dip-type', request.form.get('dip-type'))

    return resp


@app.route('/create_diplomas', methods=["POST", "GET"])
def create_diplomas():

    group_data = dict(request.form)
    file_name = request.form.get('file-name', '')
    diploma_type = request.form.get('dip-type', '')

    users = read_users_data_from_xml(file_name)

    folder_name = request.form.get('study_group_name', 'Невідома група')

    full_folder_name = os.path.join('generated', folder_name)

    if not os.path.exists(full_folder_name):
        os.mkdir(full_folder_name)

    for user in users:
        user.update(group_data)
        create_diploma_for_user(full_folder_name, dict(user), diploma_type)

    shutil.make_archive(full_folder_name, 'zip', full_folder_name)

    # Видалити XML файл із папки tmp
    os.remove(file_name)
    # Видалити файли
    shutil.rmtree(full_folder_name, ignore_errors=True)

    return render_template('report.html', data={'download_link': folder_name + '.zip'})


@app.route('/get/<filename>')
def download(filename):

    return send_file(os.path.join('generated', filename), as_attachment=True)


@app.route('/delete/<filename>')
def delete(filename):

    os.remove(os.path.join('generated', filename))

    return redirect('/archive')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

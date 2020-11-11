#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import smtplib
import ssl
import re
import time

def get_department_list():
    departments = []
    url = 'https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-all-departments'
    departments_page = requests.get(url)
    soup = BeautifulSoup(departments_page.content, 'html.parser')
    trs = soup.table.tbody.find_all('tr')
    for i in trs:
        if '*' not in i.td.get_text():
            departments.append(i.td.get_text())
    return departments

def get_department():
    departments = get_department_list()
    while True:
        department = input("Enter the course department (e.g. MATH or CPSC): ")
        department = department.upper()
        if department not in departments:
            print("Invalid input. Please try again.")
        else:
            return department

def get_course_list(department):
    courses = []
    url = f'https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-department&dept={department}'
    courses_page = requests.get(url)
    soup = BeautifulSoup(courses_page.content, 'html.parser')
    trs = soup.table.tbody.find_all('tr')
    for i in trs:
        courses.append(i.td.get_text())
    return courses

def get_course(department):
    courses = get_course_list(department)
    while True:
        course = input("Enter the course number: ")
        course = course.upper()
        course_name = f'{department} {course}'
        if course_name not in courses:
            print("Invalid input. Please try again.")
        else:
            return course

def get_sections(department, course):
    sections, restrictions, stt, blocked, unreleased = [], [], [], [], []
    url = f'https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-course&dept={department}&course={course}'
    sections_page = requests.get(url)
    soup = BeautifulSoup(sections_page.content, 'html.parser')
    trs = soup.find_all('table')[1].find_all('tr')[1:]
    for i in trs:
        sections.append(i.find_all('td')[1].get_text())
        restrictions.append(i.find_all('td')[0].get_text())
    for i in range(len(sections)):
        if restrictions[i] == 'STT':
            stt.append(sections[i])
        elif restrictions[i] == 'Blocked':
            blocked.append(sections[i])
        elif restrictions[i] == 'Unreleased':
            unreleased.append(sections[i])
    return sections, stt, blocked, unreleased

def get_section(department, course):
    sections, stt, blocked, unreleased = get_sections(department, course)
    while True:
        section = input("Enter the course section: ")
        section = section.upper()
        section_name = f'{department} {course} {section}'
        if section_name not in sections:
            print("Invalid input. Please try again.")
        elif section_name in stt:
            print("This section is only available for registration through a Standard Timetable. Please enter a different section.")
        elif section_name in blocked:
            print("This section is blocked from registration. Please enter a different section.")
        elif section_name in unreleased:
            print("This section is unreleased. Please enter a different section.")
        else:
            return section, section_name

def restricted_seats(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    tables = soup.find_all('table')
    trs = tables[3].find_all('tr')
    if len(trs) == 4:
        return False
    else:
        while True:
            check = input("Do you meet the requirements for restricted seats in this section? Enter 'yes' or 'no': ")
            check = check.lower()
            if check == 'yes' or check == 'no':
                break
            else:
                print("Invalid input please try again.")
        return check == 'yes'

def get_email():
    regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    while True:
        email = input("Enter your email address: ")
        if re.search(regex, email):
            return email
        else:
            print("Invalid email. Please try again.")

def send_email(section_name, url, receiver_email):
    sender_email = "ubccoursebot@gmail.com"
    password = 'ubcpythoncoursebot'
    subject = f"Empty Seat Available in {section_name}"
    text = f"There is an empty seat available in {section_name}.\n{url}"
    email = f"Subject: {subject}\n\n{text}"
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, email)
        server.quit()

def main():
    department = get_department()
    course = get_course(department)
    section, section_name = get_section(department, course)
    url = f'https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-section&dept={department}&course={course}&section={section}'
    check_restricted_seats = restricted_seats(url)
    receiver_email = get_email()
    count = 0
    while True:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        tables = soup.find_all('table')
        general_seats = int(tables[3].find_all('td')[5].strong.text)
        total_seats = int(tables[3].find_all('td')[1].strong.text)
        if general_seats != 0 or check_restricted_seats and total_seats != 0:
            print(f"There is an empty seat available in {section_name}.")
            send_email(section_name, url, receiver_email)
            break
        if count % 10 == 0:
            print("Checking for seats.")
        count += 1
        time.sleep(60)

if __name__ == "__main__":
    main()
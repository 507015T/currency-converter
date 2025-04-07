#!/bin/sh

echo -e "\033[0;94mЗапуск тестов через 3"
sleep 1
echo -e "\033[0;94m2"
sleep "1"
echo -e "\033[0;94m1"
sleep 1
python3.13 manage.py test


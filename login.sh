#!/bin/bash

LOGIN_URL="http://powerbucket.herokuapp.com/accounts/login/"
SUBMISSION_URL="http://powerbucket.herokuapp.com/readings/submission/"
TIME=$1
FIRST_NUM=$2
SECOND_NUM=$3
THIRD_NUM=$4
FOURTH_NUM=$5
FIFTH_NUM=$6
YOUR_USER=$BUCKET_USER
YOUR_PASS=$BUCKET_PASSWORD
COOKIES=cookies.txt
CURL_BIN="curl -s -c $COOKIES -b $COOKIES -e $LOGIN_URL"

echo -n "Django Auth: get csrftoken ..."
$CURL_BIN $LOGIN_URL > /dev/null
DJANGO_TOKEN="csrfmiddlewaretoken=$(grep csrftoken $COOKIES | sed 's/^.*csrftoken[[:space:]]*//')"

echo -n " perform login ..."
$CURL_BIN \
    -d "$DJANGO_TOKEN&username=$YOUR_USER&password=$YOUR_PASS" \
    -X POST $LOGIN_URL

echo -n " do something while logged in ..."
$CURL_BIN \
    -d "$DJANGO_TOKEN" \
    -X GET "$SUBMISSION_URL" > /dev/null
DJANGO_TOKEN="csrfmiddlewaretoken=$(grep csrftoken $COOKIES | sed 's/^.*csrftoken[[:space:]]*//')"

$CURL_BIN \
    -d "$DJANGO_TOKEN&time=$TIME&firstNum=$FIRST_NUM&secondNum=$SECOND_NUM&thirdNum=$THIRD_NUM&fourthNum=$FOURTH_NUM&fifthNum=$FIFTH_NUM" \
    -X POST "$SUBMISSION_URL"

echo " logout"
rm $COOKIES

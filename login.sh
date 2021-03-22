#!/bin/bash

WEBSITE="http://powerbucket-test.herokuapp.com/"
LOGIN_URL=$WEBSITE"accounts/login/"
SUBMISSION_URL=$WEBSITE"readings/submission/"
SETTINGS_URL=$WEBSITE"readings/change_settings/"
YOUR_USER=$BUCKET_USER
YOUR_PASS=$BUCKET_PASS
COOKIES=cookies.txt
CURL_BIN="curl -s -c $COOKIES -b $COOKIES -e $LOGIN_URL"

# echo -n "Django Auth: get csrftoken ..."
$CURL_BIN $LOGIN_URL > /dev/null
DJANGO_TOKEN="csrfmiddlewaretoken=$(grep csrftoken $COOKIES | sed 's/^.*csrftoken[[:space:]]*//')"

# echo -n " perform login ..."
$CURL_BIN \
    -d "$DJANGO_TOKEN&username=$YOUR_USER&password=$YOUR_PASS" \
    -X POST $LOGIN_URL

# echo -n " do something while logged in ..."
if [[ "$1" == "check" ]]; then
    # check whether user wants to update the settings
    X=$($CURL_BIN \
	    -d "$DJANGO_TOKEN" \
	    -X GET "$SETTINGS_URL" | egrep -o 'name="x" value="[0-9]+"' | egrep -o '[0-9]+' )
    Y=$($CURL_BIN \
	    -d "$DJANGO_TOKEN" \
	    -X GET "$SETTINGS_URL" | egrep -o 'name="y" value="[0-9]+"' | egrep -o '[0-9]+' )
    R=$($CURL_BIN \
	    -d "$DJANGO_TOKEN" \
	    -X GET "$SETTINGS_URL" | egrep -o 'name="r" value="[0-9]+"' | egrep -o '[0-9]+' )
    CHECKED=$($CURL_BIN \
		  -d "$DJANGO_TOKEN" \
		  -X GET "$SETTINGS_URL" | grep 'name="update"' | egrep -o 'checked' )
    CALCULATE_ONLINE=$($CURL_BIN \
			   -d "$DJANGO_TOKEN" \
			   -X GET "$SETTINGS_URL" | grep 'name="calculate_online"' | egrep -o 'checked' )
    if [ ${#CHECKED} -le 1 ]
    then
	CHECKED="unchecked"
    fi
    if [ ${#CALCULATE_ONLINE} -le 1 ]
    then
	CALCULATE_ONLINE="unchecked"
    fi

    echo $CHECKED
    echo $X
    echo $Y
    echo $R
    echo $CALCULATE_ONLINE
    
elif [[ "$1" == "update" ]]; then
    $CURL_BIN \
	-d "$DJANGO_TOKEN" \
	-X GET "$SETTINGS_URL" > /dev/null
    DJANGO_TOKEN="csrfmiddlewaretoken=$(grep csrftoken $COOKIES | sed 's/^.*csrftoken[[:space:]]*//')"
    $CURL_BIN \
	-d "$DJANGO_TOKEN&x=$2&y=$3&r=$4&update=False" \
	-X POST "$SETTINGS_URL"
elif [[ "$1" == "write" ]]; then 
    TIME=$2
    FIRST_NUM=$3
    SECOND_NUM=$4
    THIRD_NUM=$5
    FOURTH_NUM=$6
    FIFTH_NUM=$7
    PIC_PATH=$8 # e.g. @pictures/joe_easy_test.jpg
    #write to the website
    
    $CURL_BIN \
	-d "$DJANGO_TOKEN" \
	-X GET "$SUBMISSION_URL" > /dev/null
    DJANGO_TOKEN="csrfmiddlewaretoken=$(grep csrftoken $COOKIES | sed 's/^.*csrftoken[[:space:]]*//')"

    $CURL_BIN \
      -X POST \
      -F $DJANGO_TOKEN \
      -F time="$TIME" \
      -F firstNum=$FIRST_NUM \
      -F secondNum=$SECOND_NUM \
      -F thirdNum=$THIRD_NUM \
      -F fourthNum=$FOURTH_NUM \
      -F fifthNum=$FIFTH_NUM \
      -F "picture="$PIC_PATH \
         $SUBMISSION_URL
    
    # $CURL_BIN \
    # 	-d "$DJANGO_TOKEN&time=$TIME&firstNum=$FIRST_NUM&secondNum=$SECOND_NUM&thirdNum=$THIRD_NUM&fourthNum=$FOURTH_NUM&fifthNum=$FIFTH_NUM" \
    # 	-X POST "$SUBMISSION_URL"
fi
rm $COOKIES

from bs4 import BeautifulSoup
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from datetime import datetime, timedelta
import os  
import sys
import time

def get_datetime(given_time):
    abs_date = given_time
    if 'day' in given_time:
        vals = given_time.split()
        abs_date = (datetime.today() - timedelta(days=int(vals[0]))).strftime('%m/%d/%Y')
    elif 'hour' in given_time:
        vals = given_time.split()
        abs_date = (datetime.today() - timedelta(hours=int(vals[0]))).strftime('%m/%d/%Y')
    elif 'min' in given_time:
        vals = given_time.split()
        abs_date = (datetime.today() - timedelta(minutes=int(vals[0]))).strftime('%m/%d/%Y')
    elif 'sec' in given_time:
        vals = given_time.split()
        abs_date = (datetime.today() - timedelta(seconds=int(vals[0]))).strftime('%m/%d/%Y')
    abs_date = datetime.strptime(abs_date, '%m/%d/%Y').strftime('%Y-%m-%d')
    return abs_date

def count_divs(divs):
    count = 0
    for i in range(len(divs)):
        val = int(str(divs[i])[34])
        count += int(val) * pow(10, len(divs) - i - 1)
    return count

def count_clears(div):
    counts = div.findAll('div', attrs={'class': 'typography'})
    clear_divs = []
    attempt_divs = []
    for i in range(len(counts)):
        if str(counts[i])[34] == 's':
            clear_divs = counts[:i]
            attempt_divs = counts[i + 1:]
            break
    clears = count_divs(clear_divs)
    attempts = count_divs(attempt_divs)
    return clears, attempts

def count_typography(div):
    counts = div.findAll('div', attrs={'class': 'typography'})
    return count_divs(counts)

def write_to_csv(output_file, data):
    csv_data = ','.join(data)
    try:
        output_file.write('{}\n'.format(csv_data))
    except:
        csv_data = ','.join(data).encode('utf-8').strip()
        output_file.write('{}\n'.format(csv_data))

def parse(page, tag, class_name, data, output_file, flags):
    html = BeautifulSoup(page, 'html.parser')
    failed = html.body.find('div', attrs={'class': 'fukkin-message'})
    if failed is not None:
        # Page has no more information
        return 404
    content = html.body.findAll(tag, attrs={'class': class_name})
    if '403 Forbidden' in html.text:
        return 403
    elif '502 Bad Gateway' in html.text:
        return 502
    elif content == None or len(content) == 0:
        return 111
    for course in content:
        try:
            title = course.find('div', attrs={'class': 'course-title'}).text
            title = title.replace('"', '\'')
            title = '"{}"'.format(title)
        except AttributeError:
            title = '<No title provided by author>'
        try:
            author = course.find('div', attrs={'class': 'name'}).text
            author = author.replace('"', '\'')
            author = '"{}"'.format(author)
        except AttributeError:
            author = '<Anonymous>'
        country_div = course.find('div', attrs={'class': 'flag'})
        try:
            country = str(country_div)[17:19]
        except:
            country = '<N/A>'
        difficulty = course.find('div', attrs={'class': 'course-header'}).text.strip()
        uploaded = course.find('div', attrs={'class': 'created_at'}).text
        date_uploaded = get_datetime(uploaded)
        tag = course.find('div', attrs={'class': 'course-tag radius5'}).text
        tag = tag.replace('---', 'N/A')
        play_counts_div = course.find('div', attrs={'class': 'played-count'})
        play_count = count_typography(play_counts_div)
        like_counts_div = course.find('div', attrs={'class': 'liked-count'})
        like_count = count_typography(like_counts_div)
        clear_counts_div = course.find('div', attrs={'class': 'tried-count'})
        clear_count, attempt_count = count_clears(clear_counts_div)
        share_counts_div = course.find('div', attrs={'class': 'shared-count'})
        share_count = count_typography(share_counts_div)
        
        # You might be able to assume that all images are hosted from dypqnhofrd2x2.cloudfront.net
        # This would let you utilize the img alt for either image and not have to use find multiple types
        # The thumbnail is given as 'https://dypqnhofrd2x2.cloudfront.net/{}.jpg'.format(alt)
        # The full image is given as 'https://dypqnhofrd2x2.cloudfront.net/{}_full.jpg'.format(alt)
        course_thumbnail_div = course.find('div', attrs={'class': 'course-image'})
        course_thumbnail_url = course_thumbnail_div.find('img')['src']
        course_full_img_div = course.find('div', attrs={'class', 'course-image-full-wrapper'})
        course_full_img_url = course_full_img_div.find('img')['src']
        courseID = course_thumbnail_url[37:-4]

        course_data = [courseID, title, author, data['skin'], data['scene'], data['area'], country, tag, difficulty, date_uploaded, play_count, like_count, clear_count, attempt_count, share_count, course_thumbnail_url, course_full_img_url]
        course_data = [str(s) for s in course_data]
        write_to_csv(output_file, course_data)

        if flags[1]:
            print('courseID' + courseID)
            print('title: ' + title)
            print('author: ' + author)
            print('country: ' + country)
            print('difficulty: ' + difficulty)
            print('skin: ' + data['skin'])
            print('scene: ' + data['scene'])
            print('area: ' + data['area'])
            print('uploaded on: ' + date_uploaded)
            print('tag: ' + tag)
            print('play count: {}'.format(play_count))
            print('like count: {}'.format(like_count))
            print('clears: {} / {}'.format(clear_count, attempt_count))
            print('clear rate: {:.2f}%'.format((clear_count / attempt_count) * 100))
            print('shares: {}'.format(share_count))
            print('course thumbnail url: {}'.format(course_thumbnail_url))  
            print('course img url: {}'.format(course_full_img_url))
        
    return 200

def simple_get(url):
    try:
        with closing(get(url, stream=True)) as resp:
            return resp.content
    except RequestException:
        raise ConnectionError

def connection_error(log_file, data_file, err_code, attempt, wait_period, url, flags):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file.write('{} {} Error occured at {}\n'.format(current_time, err_code, url))
    if attempt > flags[10]:
        log_file.write('Aborting\n')
        data_file.close()
        log_file.close()
        sys.exit(err_code)
    log_file.write('{} Attempting to reconnect {}...\n'.format(current_time, attempt))
    print('{} Error: Attempting to reconnect...{}'.format(err_code, attempt))
    time.sleep(wait_period * attempt)
    return attempt + 1

def print_help():
    try:
        print('\n{:-^{}}'.format('INFO', '{}'.format(os.get_terminal_size()[0])))
    except:
        print('\n------INFO------')
    print('\nUsage:\n\tpython3 parser.py [options]')
    print('\nGeneral Options:')
    print('-i : DEBUG INFORMATION\n\tPrints all debug information')
    print('-c : COURSE INFORMATION\n\tPrints all course info')
    print('-p : PRINT PAGE\n\tPrints the page number')
    print('--verbose : VERBOSE\n\tPrints all debug information including all course info and line numbers')
    print('-ac : ALL CATEGORIESs\n\tRecords the ALL category for the following settings:\n\t\tSKIN\n\t\tSCENE\n\t\tAREA\n\t\tDIFFICULTY')
    print('-at : ALL TAGS\n\tRecords the ALL time frames and sorting methods for the ANY TAG')
    print('-AT : ALL TIMES\n\tRecords all time frames for uploading')
    print('-AS : ALL SORTING\n\tRecords all sorting methods')
    print('-E  : EVERYTHING\n\tRecords all information\n\tEquivalent to -ac -at -AT -AS\n\tNOTE: This may take a while')
    print('-lf <filename> : SPECIFY LOG\n\tSpecify a log file to overwrite\n\tLog file will write to <filename>.log')
    print('-df <filename> : SPECIFY DATA\n\tSpecify a data file to use\n\tData file will write to <filename>.csv')
    print('-d <N> : DELAY\n\tAdds a mandatory delay of N seconds for html requests (can be a float)\n\tThere is a minimum delay of 0.1 seconds for any mutlithreaded instance')
    print('-ma <N> : MAX ATTEMPTS\n\tMaximum number of attempts to reconnect until exiting')
    print('-s <i j k l m n o p> : SET VALUES\n\tSets the values for SKIN, SCENE, AREA, DIFFICULTY,\n\tTAGS, CREATED AT, and SORTING respectively')
    # print('-mt <N> : specify the max threads\n\tSpecify the maximum number of threads up to 8 that can be run\n\tNumber of threads can be 1, 2 (default), 4, or 8\n\t8 threads has an associated 0.2 second minimum delay')
    print('-help : help\n\tPrints the help screen')
    sys.exit(0)

def err_msg(err):
    print('Error: use python3 parser.py -help for more information')
    sys.exit(err)

def set_flags(args):
    flags = ['-i', '-c', '--verbose', '-p', '-ac', '-at', '-AT', '-AS', '-E', '-lf', '-df', '-d', '-ma', '-s', '-help']

    # flag_vals[0]  : Whether to print debug
    # flag_vals[1]  : Whether to print all course information
    # flag_vals[2]  : Whether to print the lines
    # flag_vals[3]  : Whether or not to record the ALL category for SKIN, SCENE, SCENE, AREA, and DIFFICULTY
    # flag_vals[4]  : Whether or not to record the ALL time frames and sorting methods for TAG
    # flag_vals[5]  : Whether to record all possibly time frames
    # flag_vals[6]  : Whether to record all possible sorting methods

    # flag_vals[7]  : File to log to
    # flag_vals[8]  : File to record data to
    # flag_vals[9]  : Delay for the html requests
    # flag_vals[10] : Maximum attempts before aborting
    # flag_vals[11] : Values based on the log file to take in i, j, ..., p

    flag_vals = [False, False, False, False, False, False, False, 'smm{}.log', 'smm{}.csv', 0, 10, [0, 0, 0, 0, 0, 0, 0, 1]]

    if len(args) < 2:
        return flag_vals

    i = 1
    while i < len(args):
        if args[i] not in flags: # Invalid flag
            err_msg(1)
        elif args[i] == flags[0]: # Debug information
            flag_vals[0] = True
        elif args[i] == flags[1]: # Course information
            flag_vals[1] = True
        elif args[i] == flags[2]: # Verbose (debug, course)
            flag_vals[0] = True
            flag_vals[1] = True
            flag_vals[2] = True
        elif args[i] == flags[3]: # Print lines
            flag_vals[2] = True
        elif args[i] == flags[4]: # All categories
            flag_vals[3] = True
        elif args[i] == flags[5]: # All tags
            flag_vals[4] = True
        elif args[i] == flags[6]: # All sorting time methods
            flag_vals[5] = True
        elif args[i] == flags[7]: # All sorting methods
            flag_vals[6] = True
        elif args[i] == flags[8]: # Everything
            flag_vals[3] = True
            flag_vals[4] = True
            flag_vals[5] = True
            flag_vals[6] = True
        elif args[i] == flags[9]: # Log file
            try:
                flag_vals[7] = args[i + 1] + '{}.log'
                i += 1
            except:
                err_msg(2)
        elif args[i] == flags[10]: # CSV file
            try:
                flag_vals[8] = args[i + 1] + '{}.csv'
                i += 1
            except:
                err_msg(2)
        elif args[i] == flags[11]: # Delay
            try:
                flag_vals[9] = max(flag_vals[9], float(args[i + 1]))
                i += 1
            except:
                err_msg(3)
        elif args[i] == flags[12]: # Attempts
            try:
                flag_vals[10] = int(args[i + 1])
                i += 1
            except:
                err_msg(3)
        elif args[i] == flags[13]: # Reset values
            try:
                vals = args[i+1:i+9]
                min_vals = [0, 0, 0, 0,  0, 0, 0,   1]
                max_vals = [5, 6, 4, 5, 15, 5, 4, 100]
                vals = [int(i) for i in vals]
                for j in range(len(vals)):
                    if vals[j] < min_vals[j]:
                        err_msg(3)
                    elif vals[j] > max_vals[j]:
                        err_msg(3)
                    i += len(str(vals[j]))
                flag_vals[11] = vals
            except:
                err_msg(3)
        elif args[i] == flags[14]:
            print_help()
        i += 1
    return flag_vals

def worker(thread, flags, overwrite):
    try:
        skins = ['mario_bros', 'mario_bros3', 'mario_world', 'mario_bros_u']
        scenes = ['ground', 'underground', 'underwater', 'gohst_house', 'airship', 'castle']
        areas = ['jp', 'us', 'eu', 'others']
        difficulties = ['easy', 'normal', 'expert', 'super_expert']
        tag_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] # += ['']
        tags = ['Automatic', 'Music', 'Puzzle', 'Gimmick', 'Dash', 'Remix', 'Thumbnail', 'Costume', 'Yoshi', 'Theme', 'Speedrun', 'Autoscroll', 'Shoot-\'em-up', 'Track', 'Traditional'] # += ['N/A']

        if flags[3]: # Duplicates, optional
            skins += ['']
            scenes += ['']
            areas += ['']
            difficulties += ['']

        created_at = ['past_month', 'before_one_month']
        if flags[5]: # Duplicates, not recommended
            created_at += ['past_day', 'past_week', '']

        # To improve the amount of time taken, just pick one of these and remove the others
        # ['like_rate_desc', 'liked_count_desc', 'clear_rate_asc', 'sns_shared_count_desc', 'created_at_desc']
        sorting_methods = ['like_rate_desc']
        if flags[6]: # Duplicates, not recommended
            sorting_methods += ['liked_count_desc', 'clear_rate_asc', 'sns_shared_count_desc', 'created_at_desc']

        if flags[4]:
            tag_ids = ['']
            tags = ['N/A']
            created_at = ['past_week', 'past_month', 'before_one_month']
            sorting_methods = ['like_rate_desc', 'liked_count_desc', 'clear_rate_asc', 'sns_shared_count_desc', 'created_at_desc']
        
        pages = 100

        # One can infer all information about the current page using the url
        log_file_name = flags[7].format('')
        # Note: this will override the previous log file
        log_file = open(log_file_name, 'w')

        data_file_name = flags[8].format('')
        if overwrite:
            data_file = open(data_file_name, 'w')
            titles = ['courseID', 'title', 'author', 'skin', 'scene', 'region', 'country', 'tag', 'difficulty', 'uploaded', 'plays', 'likes', 'clears', 'attempts', 'shares', 'thumb_url', 'full_url']
            csv_titles = ','.join(titles)
            data_file.write('{}\n'.format(csv_titles))
        else:
            data_file = open(data_file_name, 'w+')
        
        wait_period = 60
        attempt = 1

        reset_vals = flags[11]
        
        if flags[0]:
            print('Reading data...')
        log_file.write('{} Recording data to {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), data_file_name))
        for i in range(reset_vals[0], len(skins)):
            log_file.write('{} Using skin: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), skins[i]))
            if flags[0]:
                print('Using skin: {}'.format(skins[i]))
            for j in range(reset_vals[1], len(scenes)):
                log_file.write('{} Using scene: {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), scenes[j]))
                if flags[0]:
                    print('With scene: {}'.format(scenes[j]))
                for k in range(reset_vals[2], len(areas)):
                    log_file.write('{} Using area: {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), areas[k]))
                    if flags[0]:
                        print('In area: {}'.format(areas[k]))
                    for l in range(reset_vals[3], len(difficulties)):
                        log_file.write('{} Using difficulty: {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), difficulties[l]))
                        if flags[0]:
                            print('On difficulty: {}'.format(difficulties[l]))
                        for m in range(reset_vals[4], len(tag_ids)):
                            log_file.write('{} Using tag: {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), tags[m]))
                            if flags[0]:
                                print('With tag: {}'.format(tags[m]))
                            for n in range(reset_vals[5], len(created_at)):
                                log_file.write('{} Uploaded: {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), created_at[n]))
                                if flags[0]:
                                    print('That were uploaded: {}'.format(created_at[n]))
                                data = {'skin': skins[i], 'scene': scenes[j], 'area': areas[k]}
                                for o in range (reset_vals[6], len(sorting_methods)):
                                    log_file.write('{} Using sorting method: {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), sorting_methods[o]))
                                    if flags[0]:
                                        print('Using sorting method: {}'.format(sorting_methods[o]))
                                    p = reset_vals[7]
                                    while p < pages + 1:
                                        if flags[2]:
                                            print('On page number: {}'.format(p))

                                        # Added delay between requests
                                        time.sleep(flags[9])
                                        
                                        url = 'https://supermariomakerbookmark.nintendo.net/search/result?page={}&q%5Bskin%5D={}&q%5Bscene%5D={}&q%5Barea%5D={}&q%5Bdifficulty%5D={}&q%5Btag_id%5D={}&q%5Bcreated_at%5D={}&q%5Bsorting_item%5D={}'.format(p, skins[i], scenes[j], areas[k], difficulties[l], tag_ids[m], created_at[n], sorting_methods[o])
                                        
                                        try:
                                            page = simple_get(url)
                                        except ConnectionError:
                                            attempt = connection_error(log_file, data_file, 403, attempt, wait_period, url, flags)
                                            continue

                                        log_file.write('\nCurrently on page {}\n'.format(url))
                                        log_file.write('i: {}, j: {}, k: {}, l: {}, m: {}, n: {}, o: {}, p: {}\n'.format(i, j, k, l, m, n, o, p))

                                        status = parse(page, 'div', 'course-card', data, data_file, flags)
                                        if status != 200:
                                            if status == 404:
                                                log_file.write('No data exists at {}\n'.format(url))
                                                log_file.write('Skipping pages after page: {}\n'.format(p))
                                            elif status == 403:
                                                attempt = connection_error(log_file, data_file, 403, attempt, wait_period, url, flags)
                                                continue
                                            elif status == 502:
                                                log_file.write('Page took too long {}\n'.format(url))
                                                log_file.write('Skipping pages after page: {}\n'.format(p))
                                                # attempt = connection_error(log_file, data_file, 502, attempt, wait_period, url, flags)
                                                # continue
                                            elif status == 111: # No content error
                                                attempt = connection_error(log_file, data_file, 111, attempt, wait_period, url, flags)
                                                continue
                                            else: # Unknown error
                                                attempt = connection_error(log_file, data_file, 999, attempt, wait_period, url, flags)
                                                continue
                                            attempt = 1
                                            break
                                        p += 1
                                    reset_vals[7] = 1
                                reset_vals[6] = 0
                            reset_vals[5] = 0
                        reset_vals[4] = 0
                    reset_vals[3] = 0
                reset_vals[2] = 0
            reset_vals[1] = 0
        data_file.close()
        log_file.write('\nFinished!\n')
        log_file.close()
    except KeyboardInterrupt:
        data_file.close()
        log_file.write('\n{} Forceful close\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        log_file.close()
        print('\nSafely exiting')
        sys.exit(5)

    print('\nFinished')

def main():
    flags = set_flags(sys.argv)

    overwrite = input('If a data file already exists, do you wish to overwrite the data?\n\t(Select y if you wish to create a new file)  [y / n]: ')
    while overwrite.lower() not in ('y', 'yes', 'n', 'no'):
        overwrite = input('Please enter y or n: ')
    
    if overwrite.lower() in ('y', 'yes'):
        overwrite = True
    else:
        overwrite = False

    def_reset_vals = [0, 0, 0, 0, 0, 0, 0, 1]

    if flags[11] != def_reset_vals:
        worker(None, flags, overwrite)
    else:
        # Threading
        worker(None, flags, overwrite)

if __name__ == '__main__':
    main()

# As it appears:
# 'https://supermariomakerbookmark.nintendo.net/search/result?page=<page>&q[skin]=&q[scene]=&q[area]=&q[difficulty]=&q[tag_id]=&q[created_at]=&q[sorting_item]=<sorting method>'
# As it should be written
# 'https://supermariomakerbookmark.nintendo.net/search/result?page=<page>&q%5Barea%5D=&q%5Bcreated_at%5D=&q%5Bdifficulty%5D=&q%5Bscene%5D=&q%5Bskin%5D=mario_bros&q%5Bsorting_item%5D=<sorting method>&q%5Btag_id%5D='
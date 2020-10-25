# Imports
import requests as requests;
import json;
from time import time, sleep;
import pandas as pd;


# Functions
def download(beginning=0, end=time()):
	"""
	:param beginning: The time (since epoch) to start with
	:param end: The time (since epoch) to start at
	:return: json of all posts
	"""
	try:
		return json.loads(requests.get("https://api.pushshift.io/reddit/search/submission/?subreddit=wallstreetbets&sort=asc&sort_type=created_utc&after=%.0f&before=%.0f&size=1000" %(beginning, end)).text);
	except:
		print("HTTP Response: ", requests.get("https://api.pushshift.io/reddit/search/submission/?subreddit=wallstreetbets&sort=asc&sort_type=created_utc&after=%.0f&before=%.0f&size=1000" %(beginning, end)).status_code);
		sleep(0.1);
		return download(beginning);


def analyze(post):
	"""
	:param post: The JSON of the post
	:return: whether to save the posts
	"""
	importantWords = ["long", "short", "buy", "sell", "up", "down", "blowing", "bull", "bear", "moon", "p ", "c "];
	allowedFlairs = ["dd", "fundamentals"]
	if any([word in post["title"].lower() for word in importantWords]):
		return True;
	try:
		if post["selftext"] == "":
			return False;
		elif any([word in post["selftext"].lower() for word in importantWords]):
			return True;
		elif post["link_flair_richtext"][0]['e'] != "text":
			return False;
		elif any([word in post["link_flair_richtext"][0]['t'].lower() for word in allowedFlairs]):
			return True;
		return False;
	except:
		return False;



# Main method
previousStartingTime = -1;
startingTime = 0;
savedPosts = [];
columns = ["Author", "Time", "Link", "Text", "Title", "Flair", "Score"];
while True:
	print("Starting Download", startingTime);
	allPosts = download(beginning=startingTime)['data'];
	print("Download Complete");

	previousStartingTime = startingTime;
	for post in allPosts:
		try:
			startingTime = allPosts[-1]['created_utc'];
			break;
		except:
			print("Time issue")
			pass;

	# Loop through posts
	for post in allPosts:
		# print(post);
		if analyze(post):
			try:
				savedPosts.append([post["author"].lower(), post["created_utc"], post["full_link"].lower(), post["selftext"].lower(), post["title"].lower(), post["link_flair_richtext"][0]['t'].lower(), post["score"]]);
			except KeyError as e:
				if e.args[0] == "link_flair_richtext":
					savedPosts.append([post["author"].lower(), post["created_utc"], post["full_link"].lower(), post["selftext"].lower(), post["title"].lower(), "legacy", post["score"]]);
				else:
					pass;
			except IndexError:
				savedPosts.append([post["author"].lower(), post["created_utc"], post["full_link"].lower(), post["selftext"].lower(), post["title"].lower(), "legacy", post["score"]]);

	print(len(savedPosts));
	if len(savedPosts) > 0 and previousStartingTime == startingTime:
		break;
	sleep(0.45);

# Save
pd.DataFrame(savedPosts, columns=columns).to_csv("raw_posts.csv", chunksize=1000);
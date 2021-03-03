# Imports
import pandas as pd;
from datetime import datetime, timedelta;
import string;
from calendar import monthrange;
import yfinance as yf;


# Functions
def prelimCheck(post):
	"""
	:param post: post
	:return: If the post has any suspect options
	"""
	callPutList = [str(i) + "p" for i in range(0, 10)] + [str(i) + "c" for i in range(0, 10)];
	try:
		return any([word in post[4].lower().replace("\n", " ").replace("\t", " ").replace("\r", " ") for word in callPutList]) or any([word in post[5].lower().replace("\n", " ").replace("\t", " ").replace("\r", " ") for word in callPutList]);
	except:
		return False


def calcReturn(ticker, date, strike, call, maxTime=1612563213):
	"""
	Return the result of an option trade
	:param ticker:
	:param date:
	:param strike:
	:param call: True if call
	:return: result or None
	"""
	try:
		if datetime(day=date.day, month=date.month, year=date.year).timestamp() <=0:
			return None;
		elif datetime(day=date.day, month=date.month, year=date.year).timestamp() > maxTime:
			return ["Not Expired", "Active"];
		data = yf.download(ticker.upper(), date.strftime("%Y-%m-%d"), (date + timedelta(days=1)).strftime("%Y-%m-%d"), progress=False)
		if abs(strike - data["Close"][0]) > 100 and (abs(strike - data["Close"][0])/data["Close"][0] > 10 or abs(strike - data["Close"][0])/data["Close"][0] < .1):
			return None;
		if call:
			if abs(strike - data["Close"][0]) < 0.5:
				return [data["Close"][0], "ATM"];
			elif strike > data["Close"][0]:
				return [data["Close"][0], "ITM"];
			else:
				return [data["Close"][0], "OTM"];
		else:
			if abs(strike - data["Close"][0]) < 0.5:
				return [data["Close"][0], "ATM"];
			elif strike < data["Close"][0]:
				return [data["Close"][0], "ITM"];
			else:
				return [data["Close"][0], "OTM"];
	except Exception as e:
		print(e)
		return None;


def calcDate(date, postTime):
	"""
	:param date: String of expire date
	:param postTime: Time the post was posted
	:return: time float
	"""
	date = date.replace(".", ".")
	date = ''.join(e for e in date if e.isalnum() or e == "/");
	try:
		monthStartList = ["jan", "feb", "may", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
		if date.count("/") == 1:
			date = date.split("/");
			month = int(date[0]);
			day = int(date[1]);
			postDate = datetime.fromtimestamp(int(postTime));
			if month <= postDate.month or (month == postDate.month and day < postDate.day):
				return datetime(postDate.year + 1, month, day).date();
			else:
				return datetime(postDate.year, month, day).date();
		elif date.count("/") == 2:
			date = date.split("/");
			month = int(date[0]);
			day = int(date[1]);
			year = int(date[2]);
			if len(date[2]) == 2:
				if len(date[0]) == 4:
					year = int(date[0]);
					month = int(date[1]);
					day = int(date[2]);
				else:
					year += 2000;
			return datetime(year, month, day).date();
		elif any([date.startswith(startOfMonth) for startOfMonth in monthStartList]):
			monthValue = [date.startswith(startOfMonth) for startOfMonth in monthStartList];
			month = monthValue.index(True) + 1;
			dateStart = False;
			day = "";
			for i in date:
				if i in string.ascii_letters:
					if dateStart:
						break;
				elif i.isdigit():
					if dateStart:
						dateStart = True;
						day += i;
			if day == "":
				postDate = datetime.fromtimestamp(int(postTime));
				return datetime(postDate.year, month, monthrange(postDate.year, month)[1]).date();
			return calcDate(month + "/" + day, postTime);
		return None;
	except:
		return None;


def convertToTrade(text, tickers, id, author, time):
	"""
	Converts text to trade
	:param text: text to analyze
	:param tickers: list of stock tickers
	:return: Trade (list) [postId, postAuthor, time, ticker, call/put, strike, expiration]
	"""
	monthStartList = ["ja", "fe", "ma", "ap", "ju", "au", "se", "oc", "no", "de"];
	trades = [];
	failed = [];
	text = str(text).lower().replace("\n", " ").replace("\t", " ").replace("\r", " ").split();
	for word in text:
		opType = None;
		strike = None;
		expire = None;
		if word in tickers:
			# So we know a ticker is in this section of text, now we want to see what the trade is

			for wor1 in text[text.index(word) + 1:text.index(word) + 4]:
				if "/" in wor1:
					# This must be a date
					expire = calcDate(wor1, time);
					if wor1.endswith("c"):
						opType = "c";
					elif wor1.endswith("p"):
						opType = "p";
				elif any([wor1.startswith(month) for month in monthStartList]):
					# Date but different format
					expire = calcDate(wor1, time);
					if wor1.endswith("c"):
						opType = "c";
					elif wor1.endswith("p"):
						opType = "p";
				elif wor1.count(".") > 1:
					# Date but different format
					expire = calcDate(wor1, time);
					if wor1.endswith("c"):
						opType = "c";
					elif wor1.endswith("p"):
						opType = "p";
				elif wor1.startswith("$"):
					# Strike price but it starts with $
					strike = wor1[1:];
					if wor1.endswith("c"):
						strike = wor1[1:-1];
						opType = "c";
					elif wor1.endswith("p"):
						strike = wor1[1:-1];
						opType = "p";
				elif wor1.isnumeric():
					# Strike price but its just number
					strike = wor1;
				elif wor1[:-1].isnumeric():
					# Strike price but it ends in type
					strike = wor1[:-1];
					if wor1.endswith("c"):
						opType = "c";
					elif wor1.endswith("p"):
						opType = "p";
				elif wor1[1:-1].isnumeric():
					# Strike price but it ends in type
					strike = wor1[:-1];
					if wor1.endswith("c"):
						opType = "c";
					elif wor1.endswith("p"):
						opType = "p";
			if all([val is not None for val in [word, opType, strike, expire]]):
				try:
					strike = float(strike);
					if word.startswith("$"):
						word = word[1:];
					res = calcReturn(word, expire, strike, opType == "c");
					if res is not None:
						trades.append([id, author, datetime.fromtimestamp(int(time)), word, opType, strike, expire, res[1], round(res[0])]);
					else:
						failed.append([word, text, [val is not None for val in [word, opType, strike, expire]].count(True)]);
				except:
					failed.append([word, text, [val is not None for val in [word, opType, strike, expire]].count(True)]);
			else:
				failed.append([word, text, [val is not None for val in [word, opType, strike, expire]].count(True)]);
	return trades, failed;


def convertToTrade1(post):
	"""
	This converts a post to trade based on whether it says price than "c" or "p" (123c or 456p)
	:param post: post
	:return: Trade (list) [postId, postAuthor, time, ticker, call/put, strike, expiration]
	"""
	monthStartList = ["ja", "fe", "ma", "ap", "ju", "au", "se", "oc", "no", "de"]
	callList = [str(i) + "c " for i in range(0, 10)];
	putList = [str(i) + "p " for i in range(0, 10)];
	trades = [];

	# Title
	title = post[5].lower().replace("\n", " ").replace("\t", " ").replace("\r", " ")
	numberOfCalls = 0;
	for strin in callList:
		numberOfCalls += title.count(strin);
	numberOfPuts = 0;
	for strin in putList:
		numberOfPuts += title.count(strin);
	total = numberOfCalls + numberOfPuts;

	if title == "thoughts on aapl 500c jan21":
		print("time");

	index = 0;
	for i in range(numberOfCalls):
		type = "c";
		index = title.find("c ", index+1);
		startingNumberIndex = 0
		for x in range(1, 10):
			if not (title[index - x].isnumeric() or title[index - x] == "."):
				startingNumberIndex = index - x + 1;
				if title[index - x] == "/":
					for x2 in range(1, 10):
						if title[index - x - x2] == " ":
							index = index - x - x2;
							break;
					for x in range(1, 10):
						if title[index - x] == " ":
							startingNumberIndex = index - x + 1;
							break;
					title[:index] + "c" + title[index:];
					index = index + 1;
				break;

		if 0 < startingNumberIndex < index:
			strike = title[startingNumberIndex:index];
			titleWords = title.split(" ");
			for word in titleWords:
				if strike + "c" in word:
					wordIndex = titleWords.index(word);

			expire = 0;
			try:
				if "/" in titleWords[wordIndex + 1] or "." in titleWords[wordIndex + 1]:
					expire = calcDate(titleWords[wordIndex + 1]);
				elif "ex" in titleWords[wordIndex + 1] or "for" in titleWords[wordIndex + 1]:
					if "/" in titleWords[wordIndex + 2] or "." in titleWords[wordIndex + 2]:
						expire = calcDate(titleWords[wordIndex + 2]);
					elif "'" in titleWords[wordIndex + 2]:
						expire = calcDate(titleWords[wordIndex + 2]);
					elif any([month in titleWords[wordIndex + 2] for month in monthStartList]):
						expire = calcDate(titleWords[wordIndex + 2] + " " + titleWords[wordIndex + 3]);
				elif any([month in titleWords[wordIndex + 1] for month in monthStartList]):
					expire = calcDate(titleWords[wordIndex + 1] + " " + titleWords[wordIndex + 2]);
				elif "/" in titleWords[wordIndex - 1] or "." in titleWords[wordIndex - 1]:
					expire = calcDate(titleWords[wordIndex - 1]);
				elif "/" in titleWords[wordIndex - 2] or "." in titleWords[wordIndex - 2]:
					expire = calcDate(titleWords[wordIndex - 2]);
			except:
				expire = 0;

			if expire != 0:
				ticker = titleWords[wordIndex - 1];
				if "/" in ticker:
					ticker = titleWords[wordIndex - 2];
				trades.append([post[0], post[1], post[2], ticker, type, float(strike), expire]);
			else:
				print(title);

	index = 0;
	for i in range(numberOfPuts):
		type = "p";
		index = title.find("p ", index + 1);
		startingNumberIndex = 0
		for x in range(5):
			if not (title[index - x].isnumeric() or title[index - x] == "."):
				startingNumberIndex = index - x + 1;
				if title[index - x] == "/":
					for x2 in range(1, 10):
						if title[index - x - x2] == " ":
							index = index - x - x2;
							break;
					for x in range(1, 10):
						if title[index - x] == " ":
							startingNumberIndex = index - x + 1;
							break;
					title[:index] + "p" + title[index:];
					index = index + 1;
				break;

		if 0 < startingNumberIndex < index:
			strike = title[startingNumberIndex:index];
			titleWords = title.split(" ");
			for word in titleWords:
				if strike + "p" in word:
					wordIndex = titleWords.index(word);

			expire = 0;
			try:
				if "/" in titleWords[wordIndex + 1] or "." in titleWords[wordIndex + 1]:
					expire = calcDate(titleWords[wordIndex + 1]);
				elif "ex" in titleWords[wordIndex + 1] or "for" in titleWords[wordIndex + 1]:
					if "/" in titleWords[wordIndex + 2] or "." in titleWords[wordIndex + 2]:
						expire = calcDate(titleWords[wordIndex + 2]);
					elif "'" in titleWords[wordIndex + 2]:
						expire = calcDate(titleWords[wordIndex + 2]);
					elif any([month in titleWords[wordIndex + 2] for month in monthStartList]):
						expire = calcDate(titleWords[wordIndex + 2] + " " + titleWords[wordIndex + 3]);
				elif any([month in titleWords[wordIndex + 1] for month in monthStartList]):
					expire = calcDate(titleWords[wordIndex + 1] + " " + titleWords[wordIndex + 2]);
				elif "/" in titleWords[wordIndex - 1] or "." in titleWords[wordIndex - 1]:
					expire = calcDate(titleWords[wordIndex - 1]);
				elif "/" in titleWords[wordIndex - 2] or "." in titleWords[wordIndex - 2]:
					expire = calcDate(titleWords[wordIndex - 2]);
			except:
				expire = 0;

			if expire != 0:
				ticker = titleWords[wordIndex - 1];
				if "/" in ticker:
					ticker = titleWords[wordIndex - 2];
				trades.append([post[0], post[1], post[2], ticker, type, float(strike), expire]);
			else:
				print(title);

	# Text
	text = post[4].lower().replace("\n", " ").replace("\t", " ").replace("\r", " ")
	numberOfCalls = 0;
	for strin in callList:
		numberOfCalls += text.count(strin);
	numberOfPuts = 0;
	for strin in putList:
		numberOfPuts += text.count(strin);
	total = total + numberOfCalls + numberOfPuts;

	index = 0;
	for i in range(numberOfCalls):
		type = "c";
		index = text.find("c ", index+1);
		startingNumberIndex = 0
		for x in range(5):
			if not (text[index - x].isnumeric() or text[index - x] == "."):
				startingNumberIndex = index - x + 1;
				if text[index - x] == "/":
					for x2 in range(1, 10):
						if text[index - x - x2] == " ":
							index = index - x - x2;
							break;
					for x in range(1, 10):
						if text[index - x] == " ":
							startingNumberIndex = index - x + 1;
							break;
					text[:index] + "c" + text[index:];
					index = index + 1;
				break;

		if 0 < startingNumberIndex < index:
			strike = text[startingNumberIndex:index];
			textWords = text.split(" ");
			for word in textWords:
				if strike + "c" in word:
					wordIndex = textWords.index(word);

			expire = 0;
			try:
				if "/" in textWords[wordIndex + 1] or "." in textWords[wordIndex + 1]:
					expire = calcDate(textWords[wordIndex + 1]);
				elif "ex" in textWords[wordIndex + 1] or "for" in textWords[wordIndex + 1]:
					if "/" in textWords[wordIndex + 2] or "." in textWords[wordIndex + 2]:
						expire = calcDate(textWords[wordIndex + 2]);
					elif "'" in textWords[wordIndex + 2]:
						expire = calcDate(textWords[wordIndex + 2]);
					elif any([month in textWords[wordIndex + 2] for month in monthStartList]):
						expire = calcDate(textWords[wordIndex + 2] + " " + textWords[wordIndex + 3]);
				elif any([month in textWords[wordIndex + 1] for month in monthStartList]):
					expire = calcDate(textWords[wordIndex + 1] + " " + textWords[wordIndex + 2]);
				elif "/" in textWords[wordIndex - 1] or "." in textWords[wordIndex - 1]:
					expire = calcDate(textWords[wordIndex - 1]);
				elif "/" in textWords[wordIndex - 2] or "." in textWords[wordIndex - 2]:
					expire = calcDate(textWords[wordIndex - 2]);
			except:
				expire = 0;

			if expire != 0:
				ticker = textWords[wordIndex - 1];
				if "/" in ticker:
					ticker = textWords[wordIndex - 2];
				trades.append([post[0], post[1], post[2], ticker, type, float(strike), expire]);
			else:
				print(text);

	index = 0;
	for i in range(numberOfPuts):
		type = "p";
		index = text.find("p ", index + 1);
		startingNumberIndex = 0
		for x in range(5):
			if not (text[index - x].isnumeric() or text[index - x] == "."):
				startingNumberIndex = index - x + 1;
				if text[index - x] == "/":
					for x2 in range(1, 10):
						if text[index - x - x2] == " ":
							index = index - x - x2;
							break;
					for x in range(1, 10):
						if text[index - x] == " ":
							startingNumberIndex = index - x + 1;
							break;
					text[:index] + "p" + text[index:];
					index = index + 1;
				break;

		if 0 < startingNumberIndex < index:
			strike = text[startingNumberIndex:index];
			textWords = text.split(" ");
			for word in textWords:
				if strike + "p" in word:
					wordIndex = textWords.index(word);

			expire = 0;
			try:
				if "/" in textWords[wordIndex + 1] or "." in textWords[wordIndex + 1]:
					expire = calcDate(textWords[wordIndex + 1]);
				elif "ex" in textWords[wordIndex + 1] or "for" in textWords[wordIndex + 1]:
					if "/" in textWords[wordIndex + 2] or "." in textWords[wordIndex + 2]:
						expire = calcDate(textWords[wordIndex + 2]);
					elif "'" in textWords[wordIndex + 2]:
						expire = calcDate(textWords[wordIndex + 2]);
					elif any([month in textWords[wordIndex + 2] for month in monthStartList]):
						expire = calcDate(textWords[wordIndex + 2] + " " + textWords[wordIndex + 3]);
				elif any([month in textWords[wordIndex + 1] for month in monthStartList]):
					expire = calcDate(textWords[wordIndex + 1] + " " + textWords[wordIndex + 2]);
				elif "/" in textWords[wordIndex - 1]  or "." in textWords[wordIndex - 1]:
					expire = calcDate(textWords[wordIndex - 1]);
				elif "/" in textWords[wordIndex - 2]   or "." in textWords[wordIndex - 2]:
					expire = calcDate(textWords[wordIndex - 2]);
			except:
				expire = 0;

			if expire != 0:
				ticker = textWords[wordIndex - 1];
				if "/" in ticker:
					ticker = textWords[wordIndex - 2];
				trades.append([post[0], post[1], post[2], ticker, type, float(strike), expire]);
			else:
				print(text);

	return [trades, total];






# Main Method
posts = pd.read_csv("raw_posts.csv").values.tolist();
tickers = [str(ticker).lower() for ticker in pd.read_csv("nasdaqtraded.txt", sep="|")["Symbol"].values.tolist()];
tickers += ["$" + ticker for ticker in tickers];
del tickers[tickers.index("a")], tickers[tickers.index("$a")];
del tickers[tickers.index("an")], tickers[tickers.index("$an")];
del tickers[tickers.index("at")], tickers[tickers.index("$at")];
del tickers[tickers.index("jan")], tickers[tickers.index("$jan")];
del tickers[tickers.index("all")], tickers[tickers.index("$all")];
del tickers[tickers.index("it")], tickers[tickers.index("$it")];
del tickers[tickers.index("or")], tickers[tickers.index("$or")];

posts = list(filter(prelimCheck, posts));
trades = [];
failed = [];
total = 0;

for post in posts:
	ts = convertToTrade(post[5], tickers, post[0], post[1], post[2]);
	trades += ts[0];
	failed += ts[1];
	ts = convertToTrade(post[4], tickers, post[0], post[1], post[2]);
	trades += ts[0];
	failed += ts[1];

print(len(trades));
pd.DataFrame(trades, columns=["Post Id", "Post Author", "Time", "Ticker", "Call/Put", "Strike", "Expiration", "Result (ITM/OTM)", "Result (Close Price on Expire)"]).to_csv("option_trades.csv", chunksize=1000);
print("Complete");
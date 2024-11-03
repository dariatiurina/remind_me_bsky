# Remind Me Later bot in Bluesky using Bluesky API

The main topic of the project is utilizing Bluesky API and threading to make this bot run a full day without leaving or losing any posts and notifications.

1. How to make it run?
- The project is run as a python project, so you need to run those functions:
  - python main.py - this will run the program on your computer.
2. How to communicate with a bot?
- This bot is a normal account in Bluesky by the handle @remind-me-pyt.bsky.social.
- To make it remember any post you want you just need to reply to the post you want to be reminded of with a @remind-me-pyt.bsky.social (mention the bot in a reply to a post).
- By default, the bot will remind you to post in one day, however, you can change it by adding to the post date or printing "in" with a period (for example: in 3 years).
  - Please, be aware that day comes first in the date! Example: 01.06.2024 - June 1, 2024. 
- After this bot will reply to you with the date in UTC-0 when you will be reminded of this post.
- In order to make a reminder with any time period (e.g. every month) just add to the post "every" and period (example: every 2 months).
- If you want to make it so that another person will be reminded add their handle to the post. (You can add as many, as you would like, however, be aware of the maximum of 300 characters for one post).
  - Please be aware that you must put those handles as mentions, not just @ + handle of an account.
3. When you will be reminded?
The bot will resend the post when you tell it to do it.
- The first post will be with all of the people, who made this post, who made this reminder and who were supposed to be reminded.
- The reply to this post (or the last one in a thread if a reminder held a lot of people to remind) will be the original post including photos and gifs (and their alts) that were a part of the original post.
4. Can I make bot forget some posts?
- Yes, you can.
- To do so, you need to reply to your original post with reminder (the first one that you made with @remind-me-pyt.bsky.social) with a 'delete'. Bot will delete your post from the database and you will not get a reminder.
5. How to run tests?
- python -m pytest - this will run all tests
- If you want to check what tests you want to run, every existing test in the folder tests.
6. How can I make a statistics?
- To create a graph you just need to run statistics.py.

NOTES:
- When creating a bot videos and local gifs were not a part of a Bluesky functionality. However, they announced that this will be implemented in the not-so-far-away future, please do remember it was not when the bot was originally made.
- Handle and app_password for the bot can be found in the .env file that is part of a GitLab project.
- Database is a local file that is also part of a GitLab repository, as well as a media folder.
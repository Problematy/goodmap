# Contributor's Guideline

## Rules

### Rule 1: Take it from issues

We keep our issues on github fresh and clean. We put there feature requests, bugs, etc.
If you want to help in developing our project - do it!

There are plenty of issues reported on github. Find one that suits you and make you change! Just rembember that...

### Rule 2: Priorities matter

Our backlog is diverse. It has both cosmetic and functional changes. We try to prioritise them.
Be prepared that issues without priority set can wait for their turn longer than you'd like it.

Best way to make sure your code will make to next release? Check if issue has milestone set and it's the closes one.

### Rule 3: Test your changes

There is nothing to say here. We write unit tests for our code, so make sure that your code is tested.

### Rule 4: Don't break it

If your PR is not passing our tests then it won't be allowed to get to our precious code.

**BIG BUT:** it might happen that there is not yet test which can check your code properly.
In this case best way of ensuring your code will be merged is to create such test.

## Exceptions

### Exception 1: Writing a test

Simple math here. If your PR contains **only** tests which makes our code more bug-resistant,
then you can treat your code as if it had the highest priority.

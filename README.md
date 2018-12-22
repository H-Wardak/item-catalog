# Item Catalog
This application provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

## How to Run?
The application is develped using Python language, leveraged Flask framework utilities and data stroed in SQLite DB.
1. Run ``` python database_setup.py ```
2. Run ``` python application.py ```
3. Run the application on Port **8000**

## Restrictions
- User can use Google Authentication API to log in to the application
- Only logged-in users can add, edit, delete items
- A user can only edit/delete his own items
- Category edit/delete not yet provided

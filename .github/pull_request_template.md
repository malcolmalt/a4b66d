# Summary

## Issue
https://github.com/malcolmalt/a4b66d/issues/1
## Description

Implemented 3 routes to the server side using the given design document.

### /api/prospect_files
POST route that allows users to upload a csv to the database to be later parsed.  
Request: multipart/form-data CSV file under 200mb  
Response: id of file and first 3 rows of the csv

### /api/prospect_files/{prospect_files_id}/prospects
POST route that takes a prospect file id and begins to parse the csv and upload the prospects to the database.  
Request: prospect file id, email index, first name index, last name index, force(to overwrite prospects), and has headers  
Response: id of file, total rows after header, rows inserted

### /api/prospect_files/{prospect_files_id}/progress
GET route that allows a user to check the progress of a prospect file.  
Request: prospect file id
Response: total rows in file, rows inserted

# Thoughts and Process

## Approach
To approach this problem I tried to follow the given design document and implement the routes as close as possible. I also tried to follow the conventions of the given project and create my files to match the style of the other routes and models.

## Trade offs
The current implementation of the CSV import has route 2 parse the CSV file, create a list of ProspectFile objects, and then use SQLAlchemy's add_all function to add all of the prospects all at once. I found that adding each row individually took much longer especially when implementing route 3. Route 3 wants to see how many rows from the CSV have been added to the database. This can be done by counting how many rows the database has before importing has started and how many it has currently. However, this approach does not account for duplicates already in the database. To make the progress count accurate we have to increment a count every time a duplicate is encountered and factor that into the total count for route 3. The count is easier to keep track of if we add all of the rows after processing the CSV rather than one at a time, but this makes route 3 unnecessary as route 2 will either enter all of the rows at once or none if it fails.

## Large files
The current implementation can insert 8000 rows in 20 seconds on my personal computer. With the max upload size being 1,000,000 rows, I believe the current implementation would be too slow. The process is limited by sending too many requests to the database using SQLAlchemy's ORM. SQLAlchemy has a faster method for inserts using Bulk_save_objects, but this function skips over many other functions, like relationships and primary key auto-increase, in favor of speed. This could be a suitable way to speed up the process, but database changes would have to be made to account for the function. There are other ways to handle large files, but this is one solution that I came across while coding the project.

## Further comments (optional)
I thought this was a well-put-together project and feel like I learned a lot from it.
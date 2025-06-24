SQL Data Cleaning and Preprocessing Cheatsheet

1. String Operations

trim/ltrim/rtrim                --Removes leading/trailing whitespace
upper/lower                     --Converts text to upper/lowercase
replace(col, old, new)          --Substitues specified text in string
length/len                      --Checks string length for validation
left/right(col, n)              --Gets leftmost/rightmost characters
substring(col, start, length)   --Extracts part of string
regexp_replace                  --Cleans text using pattern matching

2. NULL & Value Handling

coalesce(col, default_value)    --Replaces NULL with specified default
nullif(col, value)              --Returns NULL if column equals value
where col, IS NOT NULL          --Filters out NULL values
castO(col AS type)              --Converts column to different datatype

3. Numeric Operations

round(col, decimals)            --Rounds numeric values to specifics
floor/ceiling                   --Rounds down/up to nearest integer
abs()                           --Returns absolute value

4. Date/Time Operations

extract(part FROM date)         --Gets specific part of datetime
dateadd/date_add                --Adds interval to datetime
datediff                        --Calculates differences betweendates
to_date/str_to_date             --Converts strings to date
date_format                     --Formats date as specified string

5. Aggregation & Grouping

group by + count(*)             --Indentifies duplicates record paterns
group by + having               --Filters groups based on condtion
sum(col)                        --Calculates total of numeric values
avg(col)                        --Calculates arithmertic mean
min(col)                        --Finds minimum value in column
max(col)                        --Finds maximum value in column
distinct                        --Removes duplicates rows from results

6. Row Operations & Logic

row_number()                    --Assingns unique IDs to rows
case when...then...end          --Creates conditional logic for cleaning
pivot/unpivot                   --Transforms row/column structure

7. Data modifications & Structure

update table set                --Modifies existing data values
delete from                     --Removes unwanted records
with cte                        --Creates temporary result set
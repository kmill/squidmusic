from http://code.google.com/p/pyiso8601

Many file formats and standards use the ISO 8601 date format (e.g. 2007-01-14T20:34:22+00:00) to store dates in a neutral, unambiguous manner. This simple module parses the most common forms encountered and returns datetime objects.

>>> import iso8601
>>> iso8601.parse_date("2007-06-20T12:34:40+03:00")
datetime.datetime(2007, 6, 20, 12, 34, 40, tzinfo=<FixedOffset '+03:00'>)
>>> iso8601.parse_date("2007-06-20T12:34:40Z")
datetime.datetime(2007, 6, 20, 12, 34, 40, tzinfo=<iso8601.iso8601.Utc object at 0x100ebf0>)
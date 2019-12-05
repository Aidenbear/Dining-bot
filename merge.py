import csv

terms = ['chinese', 'italian', 'indian','mexican', 'american', 'japanese']
business_set = set()
new_file = 'yelp.csv'
count = 0
for term in terms:
    file_name = 'yelp_'+term+'.csv'
    with open(file_name) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        with open(new_file, 'a') as out:
            csv_one = csv.writer(out)
            for row in csv_reader:
                if count == 0:
                    csv_one.writerow(['Business_ID', 'Name', 'Address', 'Coordinates', 'Number_of_Reviews', 'Rating', 'Zip_Code', 'Cuisine'])
                    count += 1
                else:
                    if row[0] and row[0] not in business_set:
                        row.append(term)
                        csv_one.writerow(row)
                        business_set.add(row[0])
                        count += 1
                    else:
                        pass
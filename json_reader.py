import json

infile = "csvjson.json"
outfile = "bulk.json"
i = 1;
with open(infile) as f_read:
	with open(outfile, 'w') as f_write:
		data = json.load(f_read)
		for line in data:
			f_write.write('{ "index" : { "_index": "restaurants", "_type" : "Restaurant", "_id" : "')
			f_write.write('{}'.format(i))
			f_write.write('" } }\n')
			f_write.write('{}\n'.format(json.dumps(line)))
			i+=1
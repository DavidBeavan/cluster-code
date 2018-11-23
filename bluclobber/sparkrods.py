import pyspark

def get_streams(downsample=1, source="oids.txt", app="Books"):


    sc = pyspark.SparkContext(appName=app)

    oids = map(lambda x: x.strip(), list(open('oids.txt')))
    rddoids = sc.parallelize(oids)
    streams = rddoids.map(lambda x: x)
    return streams

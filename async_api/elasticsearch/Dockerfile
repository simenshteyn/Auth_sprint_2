# Don't forget to map :/usr/share/elasticsearch/data in docker-compose for persistence

FROM docker.elastic.co/elasticsearch/elasticsearch:7.13.0
EXPOSE 9200
ENV discovery.type=single-node
ENV xpack.security.enabled=false
ENV ES_JAVA_OPTS="-Xms512m -Xmx512m"

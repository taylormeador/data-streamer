#!/bin/bash

# Setup script for ELK stack configuration

echo "Setting up ELK stack configuration..."

# Create directory structure
mkdir -p elk/logstash/config
mkdir -p elk/logstash/pipeline

# Copy configuration files
echo "Creating Logstash configuration files..."

# Logstash config
cat > elk/logstash/config/logstash.yml << 'EOF'
http.host: "0.0.0.0"
xpack.monitoring.elasticsearch.hosts: [ "http://elasticsearch:9200" ]
EOF

# Logstash pipeline
cat > elk/logstash/pipeline/logstash.conf << 'EOF'
input {
  # Accept JSON logs via TCP
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  # Parse timestamp if it's a string
  if [timestamp] {
    date {
      match => [ "timestamp", "ISO8601" ]
      target => "@timestamp"
    }
  }
  
  # Ensure level is lowercase
  if [level] {
    mutate {
      lowercase => [ "level" ]
    }
  }
  
  # Add environment if not present
  if ![environment] {
    mutate {
      add_field => { "environment" => "development" }
    }
  }
  
  # Create index name based on service
  if [service] {
    mutate {
      add_field => { "[@metadata][index_name]" => "logs-%{service}-%{+YYYY.MM.dd}" }
    }
  } else {
    mutate {
      add_field => { "[@metadata][index_name]" => "logs-unknown-%{+YYYY.MM.dd}" }
    }
  }
}

output {
  # Send to Elasticsearch
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][index_name]}"
  }
  
  # Also output to stdout for debugging (optional, can remove in production)
  stdout {
    codec => rubydebug
  }
}
EOF

echo "✅ ELK configuration created successfully!"
echo ""
echo "Directory structure:"
echo "  elk/"
echo "  ├── logstash/"
echo "  │   ├── config/"
echo "  │   │   └── logstash.yml"
echo "  │   └── pipeline/"
echo "  │       └── logstash.conf"
echo ""
echo "Next steps:"
echo "1. Run this script in your project root: bash setup-elk.sh"
echo "2. Start the ELK stack: docker-compose up -d elasticsearch logstash kibana"
echo "3. Wait for services to be healthy (~60 seconds)"
echo "4. Open Kibana: http://localhost:5601"
echo "5. Create index pattern in Kibana: logs-*"

#!/bin/bash

source_directory="./assets"
code_jobs=("$source_directory"/*.py)
tag="1.1.0"

build_docker_image() {
    local code_path="$1"
    local code_file
    local code_name
    local image_size
    local image_size_mb

    code_file=$(basename "$code_path")
    code_name="${code_file%.*}"
    
    cat > Dockerfile-$code_name <<EOL
        FROM python:3.13-bookworm

        WORKDIR /code_job

        COPY ./main.py .
        COPY $code_file code.py
        COPY ./requirements.txt .

        RUN pip3 install -r requirements.txt

        ENTRYPOINT ["python3", "main.py"]
EOL

    docker build -t "glarakis99/code-job-$code_name:$tag" -f Dockerfile-$code_name "$source_directory"
    docker image tag "glarakis99/code-job-$code_name:$tag" "glarakis99/code-job-$code_name:$tag"
    docker push "glarakis99/code-job-$code_name:$tag"

    image_size=$(docker image inspect "glarakis99/code-job-$code_name:$tag" --format='{{.Size}}')
    image_size_mb=$((image_size / 1024 / 1024))

    if [[ $code_name == "bubble-sort" || $code_name == "selection-sort" || $code_name == "insertion-sort" ]]; then
        complexity="O(n^2)"
    elif [[ $code_name == "merge-sort" ]]; then
        complexity="O(n*log(n))"
    fi

    echo "('$code_name', 'code-job-$code_name', '$tag', '$complexity', $image_size_mb)," >> insert_code.sql

    rm Dockerfile-$code_name
}

echo "INSERT INTO code (name, image, tag, complexity, size_mb) VALUES" >> insert_code.sql
for code_path in "${code_jobs[@]}"; do
    if [[ $(basename "$code_path") == main.py ]]; then
        continue
    elif [[ -f $code_path ]]; then
        build_docker_image "$code_path" &
    else
        echo "No Python files found in $source_directory."
    fi
done

wait
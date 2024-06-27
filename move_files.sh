#!/bin/bash

# 确保当前目录下有tmp文件夹，如果没有则创建一个
if [ ! -d "tmp" ]; then
    mkdir tmp
fi

# 初始化计数器
files_moved=0

# 定义需要移动的文件扩展名
file_extensions=("*.txt" "*.jpeg" "*.jpg" "*.epub" "*.png")

# 遍历文件扩展名
for ext in "${file_extensions[@]}"; do
    # 移动匹配的文件到tmp文件夹
    for file in $ext; do
        if [ -e "$file" ]; then
            mv "$file" tmp/
            ((files_moved++))
        fi
    done
done

# 输出结果
echo "Successfully moved $files_moved files to the tmp folder."

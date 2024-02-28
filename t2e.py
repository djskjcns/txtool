import re
import os
import sys
from ebooklib import epub

def process_input():
    if len(sys.argv) != 3:
        print("Error: Please specify both a cover image and a text file.")
        sys.exit(1)

    image_path = None
    text_path = None
    valid_image_extensions = ['.jpg', '.jpeg', '.png']
    
    for arg in sys.argv[1:3]:
        if arg.lower().endswith('.txt'):
            if text_path is None:
                text_path = arg
            else:
                print("Error: Multiple text files provided.")
                sys.exit(1)
        elif any(arg.lower().endswith(ext) for ext in valid_image_extensions):
            if image_path is None:
                image_path = arg
            else:
                print("Error: Multiple image files provided.")
                sys.exit(1)

    if not text_path or not image_path:
        print("Error: A text file and an image file are required.")
        sys.exit(1)
  
    return text_path, image_path

def cleanse_text(text_path):
    try:
        cleansed_lines = []

        with open(text_path, 'r', encoding='utf-8') as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line:
                    cleansed_lines.append(stripped_line.lstrip())
        text = '\n'.join(cleansed_lines)
    except IOError as e:
        print(f"Error: Open {text_path} failed: {e}.")
        sys.exit(1)
    
    CHAPTER_REGEX = r'(第[\u4e00-\u9fa5零一二三四五六七八九十百千万0-9]+章)'

    text = re.sub(f'(?m){CHAPTER_REGEX}', r'\n\1', text)
    return text

def export_book(text, text_path, image_path):
    try:
        with open(image_path, 'rb') as img_file:
            cover_image = img_file.read()
    except IOError as e:
        print(f"Error: Open {image_path} failed: {e}.")
        sys.exit(1)
    
    identifier = input("Enter the book's identifier (e.g., id123456): ") or 'id123456'
    language = input("Enter the book's language: (e.g., zh-CN): ") or 'zh-CN'
    author = input("Enter the author's name (e.g., anonymous): ") or 'anonymous'

    cover_ext = os.path.splitext(os.path.basename(image_path))[1]
    text_name = os.path.splitext(os.path.basename(text_path))[0]
    
    book = epub.EpubBook()

    book.set_identifier(identifier)
    book.set_title(text_name)
    book.set_language(language)
    book.add_author(author)
    book.set_cover(file_name = f'cover{cover_ext}', content = cover_image)
    
    style = '''
    @charset "UTF-8";
    h1 {
        color: #907908;
        margin-top: 2em;
        text-align: center; 
    }
    p {
       text-indent: 2em; 
    }
    '''
    stylesheet = epub.EpubItem(uid = "style_nav", file_name = "style/nav.css", media_type = "text/css", content = style)
    book.add_item(stylesheet)

    chapters = []
    chapters_text = text.split('\n\n')

    for i, chapter_text in enumerate(chapters_text, start = 1):
        lines = chapter_text.split('\n')
        if len(lines) <= 1:
            continue
        file_name = f'chap_{i:02d}.xhtml'
        title = lines[0]
        content = '</p><p>'.join(lines[1:])
        
        chapter = epub.EpubHtml(title = title, file_name = file_name, lang = language)
        chapter.content = f'<h1>{title}</h1><p>{content}</p>'
        chapter.add_item(stylesheet)
        
        chapters.append(chapter)
        book.add_item(chapter)

    book.toc = tuple([epub.Link(chapter.file_name, chapter.title, f"chapter{i}") for i, chapter in enumerate(chapters, start = 1)])
     
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
 
    book.spine = ["nav"] + chapters

    try:
        output_path = os.path.join(os.path.dirname(text_path), text_name + '.epub')
        epub.write_epub(output_path, book, {})
        print(f"Books have been exported to：{output_path}")
    except Exception as e:
        print(f"Error: Failed to write the EPUB file: {e}")
        sys.exit(1)
    
def main():
    text_path, image_path = process_input()
    text = cleanse_text(text_path)
    export_book(text, text_path, image_path)

if __name__ == '__main__':
    main()
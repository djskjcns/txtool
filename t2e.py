import re
import os
import sys
from ebooklib import epub

CHAPTER_REGEX = r'(^第[零一二三四五六七八九十百千万0-9]+[章部卷] )'
CSS_STYLE = """
@charset "UTF-8";
h1,
h2 {
    text-align: center;
    margin: 1em 0;
    text-indent: 0;
}
p {
    text-indent: 2em;
    margin: 0.5em 0;
    line-height: 1.5em;
    text-align: justify;
}
"""

def t2e(text_file, image_file):
    # Handle image file
    with open(image_file, 'rb') as img_file:
        cover_image = img_file.read()
    
    # Create epub book
    book = epub.EpubBook()
    
    book.set_language('zh')
    book.set_cover(file_name=image_file, content=cover_image)
    book.set_title(os.path.basename(text_file).replace('.txt', ''))

    # Create CSS style
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=CSS_STYLE)
    
    # Handle text file
    # Chinese novels commonly used coding format gb18030
    try:
        with open(text_file, 'r', encoding='utf-8') as file:
            text_lines = file.readlines()
        print("The file was read successfully using the UTF-8 encoding.")
    except UnicodeDecodeError:
        with open(text_file, 'r', encoding='gb18030') as file:
            text_lines = file.readlines()
        print("The file was read successfully using the GB18030 encoding.")
    
    chapter_title = None
    book.toc = []
    book.spine = []
    collect_content = []
    
    for i, line in enumerate(text_lines, start = 1):
        stripped_line = line.strip()
        
        if not stripped_line:
            continue

        if re.search(CHAPTER_REGEX, stripped_line):
            # if collect_content:
            book = handle_chapter(chapter_title, i, collect_content, book, nav_css)
            collect_content = []
            chapter_title = stripped_line
        else:
            collect_content.append(stripped_line)

    # Add the last chapter
    book = handle_chapter(chapter_title, i, collect_content, book, nav_css)

    book.add_item(nav_css)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    return book

def handle_chapter(chapter_title, number, content, book, nav_css):
    if chapter_title:
        content = '</p><p>'.join(content[:])
    else:
        chapter_title = content[0]
        content = '</p><p>'.join(content[1:])
    file_name = f'chapter{number:02d}.xhtml'
    
    chapter = epub.EpubHtml(title=chapter_title, file_name=file_name, lang='zh', uid=f'chapter{number}')
    chapter.content = f'<h2>{chapter_title}</h2><p>{content}</p>'
    chapter.add_item(nav_css)
    
    book.toc.append(epub.Link(file_name, chapter_title, f'chapter{number}'))
    book.spine.append(chapter)
    book.add_item(chapter)
    
    return book

def main():
    if len(sys.argv) != 3:
        print("Usage: python t2e.py <txt file> <image file>")
        sys.exit(1)

    image_file, text_file = None, None
    valid_image_extensions = ['.jpg', '.jpeg', '.png']

    for arg in sys.argv[1:3]:
        ext = os.path.splitext(arg.lower())[1]
        if ext == '.txt':
            text_file = arg
        elif ext in valid_image_extensions:
            image_file = arg

    if not text_file or not image_file:
        print("Error: Text file or Image file not provided.")
        sys.exit(1)
    
    book = t2e(text_file, image_file)
    
    # Output epub file
    epub_file = text_file.replace('.txt', '.epub')
    epub.write_epub(epub_file, book, {})
    print(f"Books have been exported to: {epub_file}")

if __name__ == '__main__':
    main()
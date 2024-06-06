import re
import os
import sys
from ebooklib import epub

CHAPTER_REGEX = r'(^第[零一二三四五六七八九十百千万0-9]+[章] )'
VOLUME_REGEX = r'(^第[零一二三四五六七八九十百千万0-9]+[部卷] )'
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
    nav_css = epub.EpubItem(
        uid='style_nav',
        file_name='style/nav.css',
        media_type='text/css',
        content=CSS_STYLE
    )
    
    # Handle text file
    try:
        with open(text_file, 'r', encoding='utf-8') as file:
            text_lines = file.readlines()
        print("The file was read successfully using the UTF-8 encoding.")
    except UnicodeDecodeError:
        with open(text_file, 'r', encoding='gb18030') as file:
            text_lines = file.readlines()
        print("The file was read successfully using the GB18030 encoding.")
    
    book.toc = []
    book.spine = []
    chapter = {'title': None, 'content': []}
    volume = {'title': None, 'toc': []}
    
    for i, line in enumerate(text_lines, start=1):
        stripped_line = line.strip()
        
        if not stripped_line:
            continue

        if re.search(VOLUME_REGEX, stripped_line):
            if chapter['content']:
                book = handle_chapter(chapter, volume, i, book, nav_css)
                chapter['content'] = []
            volume = {'title': stripped_line, 'toc': []}
            book = handle_volume(volume, i, book, nav_css)
        elif re.search(CHAPTER_REGEX, stripped_line):
            if chapter['content']:
                book = handle_chapter(chapter, volume, i, book, nav_css)
            chapter = {'title': stripped_line, 'content': []}
        else:
            chapter['content'].append(stripped_line)

    # Add the last chapter
    book = handle_chapter(chapter, volume, i, book, nav_css)

    book.add_item(nav_css)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    return book

def handle_chapter(chapter, volume, number, book, nav_css):
    if chapter['title']:
        chapter['content'] = '</p><p>'.join(chapter['content'][:])
    else:
        chapter['title'] = chapter['content'][0]
        chapter['content'] = '</p><p>'.join(chapter['content'][1:])
    
    file_name = f'chapter{number:02d}.xhtml'
    c = epub.EpubHtml(
        title=chapter['title'],
        file_name=file_name,
        lang='zh',
        uid=f'chapter{number}'
    )
    c.content = f'<h2>{chapter["title"]}</h2><p>{chapter["content"]}</p>'
    c.add_item(nav_css)
    
    if volume['title']:
        volume['toc'].append(epub.Link(file_name, chapter['title'], f'chapter{number}'))
    else:
        book.toc.append(epub.Link(file_name, chapter['title'], f'chapter{number}'))
    
    book.spine.append(c)
    book.add_item(c)
    
    return book

def handle_volume(volume, number, book, nav_css):
    file_name = f'volume_{number:02d}.xhtml'
    v = epub.EpubHtml(
        title=volume['title'],
        file_name=file_name,
        lang='zh',
        uid=f'volume{number}'
    )
    v.content = f'<h1>{volume["title"]}</h1>'
    v.add_item(nav_css)

    book.toc.append((epub.Section(volume['title'], file_name), volume['toc']))
    book.spine.append(v)
    book.add_item(v)

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
    print(f"Book has been exported to: {epub_file}")

if __name__ == '__main__':
    main()
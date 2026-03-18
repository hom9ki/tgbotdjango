class ExcelProcessor:
    @staticmethod
    def process(file_bytes, file_name, report):
        try:
            editor = report(file_bytes, file_name)
            processed_stream = editor.get_stream
            new_filename = editor.get_file_name

            return processed_stream, {
                'filename': new_filename,
                'success': True,
                'message': f'Файл успешно обработан: {new_filename}!'
            }
        except Exception as e:

            return file_bytes, {
                'filename': file_name,
                'success': False,
                'error': str(e)}

"""Windows 固有操作のための PowerShell 実行ユーティリティです。"""

import subprocess
import sys


class PowerShellExecutor:
    """PowerShell コマンドを安全に実行するためのユーティリティクラスです。"""

    @staticmethod
    def execute_command(command: str, timeout: int = 30) -> str | None:
        """PowerShell コマンドを実行し、出力を返します。

        Args:
            command : 実行する PowerShell コマンドです。
            timeout : コマンド実行のタイムアウト (秒) です。

        Returns:
            コマンド出力の文字列、または実行に失敗した場合は None です。
        """
        try:
            # Windows で子プロセスのウィンドウを完全に隠すためのフラグ
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-Command", command], 
                capture_output=True, 
                text=True, 
                timeout=timeout, 
                check=False,
                startupinfo=startupinfo
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None

    @staticmethod
    def execute_script_block(commands: list[str], timeout: int = 30) -> str | None:
        """複数の PowerShell コマンドをスクリプトブロックとして実行します。

        Args:
            commands : 実行する PowerShell コマンドのリストです。
            timeout : スクリプト実行のタイムアウト (秒) です。

        Returns:
            スクリプト出力の文字列、または実行に失敗した場合は None です。
        """
        script = "; ".join(commands)
        return PowerShellExecutor.execute_command(script, timeout)

    @staticmethod
    def add_to_clipboard(text: str) -> bool:
        """PowerShell を使用して Windows クリップボードにテキストを追加します。

        Args:
            text : クリップボードに追加するテキストです。

        Returns:
            成功した場合は True、そうでない場合は False です。
        """
        escaped_text = text.replace('"', '""')
        command = f'Set-Clipboard -Value "{escaped_text}"'
        result = PowerShellExecutor.execute_command(command)
        return result is not None

    @staticmethod
    def get_clipboard_content() -> str | None:
        """PowerShell を使用して現在のクリップボードの内容を取得します。

        Returns:
            クリップボードの内容の文字列、または失敗した場合は None です。
        """
        command = "Get-Clipboard"
        return PowerShellExecutor.execute_command(command)

    @staticmethod
    def is_powershell_available() -> bool:
        """システムで PowerShell が利用可能かどうかをチェックします。

        Returns:
            PowerShell が利用可能な場合は True です。
        """
        try:
            # Windows で子プロセスのウィンドウを完全に隠すためのフラグ
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-Command", "echo 'test'"], 
                capture_output=True, 
                timeout=5, 
                check=False,
                startupinfo=startupinfo
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return False

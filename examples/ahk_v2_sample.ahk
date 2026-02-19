#Requires AutoHotkey v2.0

global SapWindowTitle := "SAP Logon"
global DataFile := "input_utf8.txt"

F2:: {
    WinActivate(SapWindowTitle)
    Sleep(250)
    Click(420, 280)
    Send("{Enter}")
    PixelGetColor(500, 320)
    Sleep(150)
}

DoExcelLookup(filePath) {
    Try {
        ; Windows-only COM example
        xl := ComObject("Excel.Application")
        wb := xl.Workbooks.Open(filePath)
        ws := wb.Sheets(1)
        value := ws.Range("A2").Value
        wb.Close(false)
        xl.Quit()
        Return value
    } Catch Error as err {
        Throw Error("Excel COM failed: " err.Message)
    }
}

ProcessText() {
    content := FileRead(DataFile, "UTF-8")
    Clipboard := content
    FileAppend(content, "output_utf8.txt", "UTF-8")
}

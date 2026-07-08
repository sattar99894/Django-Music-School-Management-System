# تابع بازگشتی برای نمایش درخت و محتوا
function Show-TreeWithContent {
    param(
        [string]$Path = ".",          # مسیر شروع (پیش‌فرض: دایرکتوری جاری)
        [string]$Indent = "",         # تورفتگی فعلی (برای نمایش درخت)
        [switch]$IncludeBinary = $false  # آیا فایل‌های باینری را هم نمایش دهد؟
    )

    # دریافت همه آیتم‌های پوشه (به‌جز موارد مخفی و سیستمی)
    $items = Get-ChildItem -Path $Path -Force -ErrorAction SilentlyContinue | Where-Object { -not ($_.Attributes -match "Hidden|System") }

    # مرتب‌سازی: پوشه‌ها اول، سپس فایل‌ها
    $sorted = $items | Sort-Object { $_.PSIsContainer } -Descending

    for ($i = 0; $i -lt $sorted.Count; $i++) {
        $item = $sorted[$i]
        $isLast = ($i -eq $sorted.Count - 1)
        $prefix = if ($isLast) { "└──" } else { "├──" }
        $newIndent = if ($isLast) { "    " } else { "│   " }

        # نمایش نام آیتم با تورفتگی
        if ($item.PSIsContainer) {
            Write-Host "$Indent$prefix $($item.Name)/" -ForegroundColor Cyan
            # فراخوانی بازگشتی برای زیرپوشه
            Show-TreeWithContent -Path $item.FullName -Indent "$Indent$newIndent" -IncludeBinary:$IncludeBinary
        } else {
            Write-Host "$Indent$prefix $($item.Name)" -ForegroundColor Yellow
            # نمایش محتوای فایل (فقط متنی)
            try {
                $content = Get-Content -Path $item.FullName -Raw -ErrorAction Stop
                if ($content -match "^\x00") {
                    if ($IncludeBinary) {
                        Write-Host "$Indent    [محتوای باینری قابل نمایش نیست]" -ForegroundColor Red
                    } else {
                        Write-Host "$Indent    [فایل باینری، رد شد]" -ForegroundColor Gray
                    }
                } else {
                    Write-Host "$Indent    محتوا:" -ForegroundColor Green
                    # نمایش محتوا با تورفتگی بیشتر
                    $lines = $content -split "`r?`n"
                    foreach ($line in $lines) {
                        Write-Host "$Indent    $line"
                    }
                }
            } catch {
                # خطا در خواندن فایل (مثلاً دسترسی یا باینری)
                Write-Host "$Indent    [نمی‌توان محتوا را خواند: $_]" -ForegroundColor Red
            }
        }
    }
}

# اجرای تابع از دایرکتوری جاری (یا مسیر دلخواه)
Show-TreeWithContent -Path "."   # <-- مسیر مورد نظر را تغییر دهید

# در صورت تمایل خروجی را در یک فایل متنی ذخیره کنید:
# Show-TreeWithContent -Path "." | Out-File -FilePath "TreeReport.txt" -Encoding UTF8
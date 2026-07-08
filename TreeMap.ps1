function Show-TreeOnly {
    param(
        [string]$Path = ".",          # مسیر شروع
        [string]$Indent = ""          # تورفتگی
    )

    # دریافت آیتم‌ها (به‌جز مخفی/سیستمی) و حذف پوشه‌های .git و .venv
    $items = Get-ChildItem -Path $Path -Force -ErrorAction SilentlyContinue |
             Where-Object { 
                 ($_.Name -notin '.git', '.venv') -and 
                 (-not ($_.Attributes -match "Hidden|System"))
             }

    # مرتب‌سازی: پوشه‌ها اول، فایل‌ها دوم
    $sorted = $items | Sort-Object { $_.PSIsContainer } -Descending

    for ($i = 0; $i -lt $sorted.Count; $i++) {
        $item = $sorted[$i]
        $isLast = ($i -eq $sorted.Count - 1)
        $prefix = if ($isLast) { "└──" } else { "├──" }
        $newIndent = if ($isLast) { "    " } else { "│   " }

        if ($item.PSIsContainer) {
            # نمایش پوشه به رنگ آبی
            Write-Host "$Indent$prefix $($item.Name)/" -ForegroundColor Cyan
            # فراخوانی بازگشتی برای زیرپوشه (این فیلتر برای زیرپوشه‌ها هم اعمال می‌شود)
            Show-TreeOnly -Path $item.FullName -Indent "$Indent$newIndent"
        } else {
            # نمایش فایل به رنگ زرد
            Write-Host "$Indent$prefix $($item.Name)" -ForegroundColor Yellow
        }
    }
}

# اجرا از مسیر جاری
Show-TreeOnly -Path "."


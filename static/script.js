document.addEventListener("DOMContentLoaded", function () {

    /* =========================
       DARK / LIGHT MODE
       ========================= */

    const themeToggle = document.getElementById("theme-toggle");
    const themeIcon = document.getElementById("theme-icon");

    // Load saved theme
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
    }

    updateIcon();


    // Toggle theme
    if (themeToggle) {

        themeToggle.addEventListener("click", function () {

            document.body.classList.toggle("dark-mode");

            const isDark =
                document.body.classList.contains("dark-mode");

            if (isDark) {
                localStorage.setItem("theme", "dark");
            } else {
                localStorage.setItem("theme", "light");
            }

            updateIcon();

        });

    }


    // Change sun/moon icon
    function updateIcon() {

        if (!themeIcon) {
            return;
        }

        const isDark =
            document.body.classList.contains("dark-mode");

        if (isDark) {

            // Moon icon
            themeIcon.innerHTML = `
                <path d="M21 12.8A9 9 0 1 1 11.2 3
                7 7 0 0 0 21 12.8z"></path>
            `;

        } else {

            // Sun icon
            themeIcon.innerHTML = `
                <circle cx="12" cy="12" r="4"></circle>
                <path d="M12 2v2"></path>
                <path d="M12 20v2"></path>
                <path d="m4.93 4.93 1.41 1.41"></path>
                <path d="m17.66 17.66 1.41 1.41"></path>
                <path d="M2 12h2"></path>
                <path d="M20 12h2"></path>
                <path d="m6.34 17.66-1.41 1.41"></path>
                <path d="m19.07 4.93-1.41 1.41"></path>
            `;

        }

    }


    /* =========================
       PDF FILE NAME
       ========================= */

    const resumeInput = document.getElementById("resume");
    const fileName = document.getElementById("file-name");
    const fileStatus = document.getElementById("file-status");

    if (resumeInput) {

         resumeInput.addEventListener("change", function () {

        if (this.files.length > 0) {

            const selectedFile = this.files[0];

            fileName.textContent = selectedFile.name;
            fileStatus.textContent = "PDF selected successfully";

        } else {

            fileName.textContent = "Upload your resume";
            fileStatus.textContent = "Click here to choose a PDF file";

        }

    });

}

});
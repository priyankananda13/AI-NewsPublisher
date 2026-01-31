const loadBtn = document.getElementById("loadBtn");
const loading = document.getElementById("loading");
const container = document.getElementById("news");

loadBtn.addEventListener("click", async () => {
    loading.classList.remove("hidden");
    container.innerHTML = "";

    try {
        const res = await fetch("/top-news");
        const data = await res.json();

        data.news.forEach(item => {
            const card = document.createElement("div");
            card.className = "news-card " + item.category.toLowerCase();
            card.style.borderTopColor = item.color;  // dynamic colored top border

            card.innerHTML = `
                <div class="card-header">
                    <i class="${item.icon} category-icon" style="color:${item.color}"></i>
                    <span class="category-text">${item.category.toUpperCase()}</span>
                </div>
                <img src="${item.image}" />
                <h3>${item.title}</h3>
                <p>${item.summary}</p>
                <div class="card-footer">
                    <a href="${item.link}" target="_blank">Read more</a>
                    <i class="speaker-icon fa-solid fa-volume-high"></i>
                </div>
            `;

            const audioPlayer = new Audio(item.audio);
            card.querySelector(".speaker-icon").addEventListener("click", () => {
                audioPlayer.currentTime = 0;
                audioPlayer.play();
            });

            container.appendChild(card);
        });
    } catch (e) {
        container.innerHTML = "<p>Error loading news.</p>";
        console.error(e);
    } finally {
        loading.classList.add("hidden");
    }
});

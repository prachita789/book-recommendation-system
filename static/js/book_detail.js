document.addEventListener("DOMContentLoaded", () => {

    const bars = document.querySelectorAll(".positive-bar");

    bars.forEach(bar => {

        const width = bar.dataset.width;

        bar.style.width = width + "%";

    });

});


const stars = document.querySelectorAll(".star");
const ratingInput = document.getElementById("selected-rating");

let selectedRating = 0;

stars.forEach((star) => {

    star.addEventListener("mouseover", () => {

        const value = Number(star.dataset.value);

        updateStars(value);

    });

    star.addEventListener("mouseout", () => {

        updateStars(selectedRating);

    });

    star.addEventListener("click", () => {

        selectedRating = Number(star.dataset.value);

        ratingInput.value = selectedRating;

        updateStars(selectedRating);

    });

});

function updateStars(rating){

    stars.forEach((star) => {

        const value = Number(star.dataset.value);

        if(value <= rating){

            star.textContent = "★";
            star.classList.add("active");

        }else{

            star.textContent = "☆";
            star.classList.remove("active");

        }

    });

}
function scrollShelf(direction){

    const shelf =
        document.getElementById("popularShelf");

    const amount = 420;

    shelf.scrollBy({
        left: direction * amount,
        behavior: "smooth"
    });

}
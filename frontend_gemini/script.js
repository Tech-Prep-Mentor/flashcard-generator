document.getElementById('fetch-decks').addEventListener('click', async () => {
    console.log('Fetch Decks button clicked');
    try {
        const response = await fetch('http://127.0.0.1:8000/deck/');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const decks = await response.json();
        console.log('Decks received:', decks);  // Check if data is received

        const decksList = document.getElementById('decks-list');
        decksList.innerHTML = '';

        decks.forEach(deck => {
            console.log('Processing deck:', deck);  // Check each deck data
            const deckElement = document.createElement('div');
            deckElement.className = 'deck';
            deckElement.innerHTML = `
                <strong>Title:</strong> ${deck.title} <br>
                <strong>ID:</strong> ${deck.id} <br>
                <button onclick="fetchCards(${deck.id})">Show Cards</button>
            `;
            decksList.appendChild(deckElement);
        });
    } catch (error) {
        console.error('Error fetching decks:', error);
    }
});

async function fetchCards() {
    console.log(`Fetching cards for deck ID 3`);
    try {
        const response = await fetch(`http://127.0.0.1:8000/card/`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const cards = await response.json();
        console.log('Cards received:', cards);

        const cardsList = document.getElementById('cards-list');
        cardsList.innerHTML = '';

        cards.forEach(card => {
            console.log('Processing card:', card);  // Check each card data
            const cardElement = document.createElement('div');
            cardElement.className = 'card';
            cardElement.innerHTML = `
                <strong>Question:</strong> ${card.question} <br>
                <strong>Answer:</strong> ${card.answer}
            `;
            cardsList.appendChild(cardElement);
        });

    } catch (error) {
        console.error('Error fetching cards:', error);
    }
}

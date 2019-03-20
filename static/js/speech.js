window.SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
const synth = window.speechSynthesis;
const recognition = new SpeechRecognition();

const icon = document.querySelector('i.fa.fa-microphone')
let inputParagraph = document.createElement('p');
let inputContainer = document.querySelector('.speech-input-box');
inputContainer.appendChild(inputParagraph);
let outputContainer = document.querySelector('.speech-output-box');
let outputParagraph = document.createElement('p');
outputContainer.appendChild(outputParagraph);
const sound = document.querySelector('.sound');

icon.addEventListener('click', () => {
  sound.play();
  dictate();
});

const dictate = () => {
  recognition.start();
  recognition.onresult = (event) => {
    const speechToText = event.results[0][0].transcript;
    
    inputParagraph.textContent = speechToText;

    if (event.results[0].isFinal) {

      
      $.ajax({
        type: "POST",
        url: "https://api.dialogflow.com/v1/query?v=20150910",
        contentType: "application/json",
        dataType: "json",
        headers: {
            "Authorization": "Bearer " + 'e18346f4fd9b4c13ac8c3658c83c247b',
        },
        data: JSON.stringify({
          "lang": "en",
          "query": speechToText,
          "sessionId": "12345",
          "timezone": "America/Denver"
        }),
        success: function(response) {
            console.log(response)
            outputParagraph.textContent = response.result.fulfillment.speech;
            synth.speak(new SpeechSynthesisUtterance(response.result.fulfillment.speech));
        },
        error: function() {
            console.log("Internal Server Error");
        }
      }); 
    } 
  }
}

const speak = (action) => {
  utterThis = new SpeechSynthesisUtterance(action());
  synth.speak(utterThis);
};
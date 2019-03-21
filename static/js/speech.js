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
    console.log(event);
    if (event.results[0].isFinal) {

      
      $.ajax({
        type: "POST",
        url: "https://dialogflow.googleapis.com/v2/projects/speech-agent-f8831/agent/sessions/123456789:detectIntent",
        contentType: "application/json",
        dataType: "json",
        headers: {
            "Authorization": "Bearer " + 'ya29.c.ElrTBhF9LCGx1ztArr4mK2pG04ONUYo4-RtFzk89mFfWSeNIyFX1prakb3DSQyVRNmTRDEe0Bpap9yaiSxah0aXCHVB6zYQv-0m6ajNam4lxkRINfCcafuARJI4',
        },
        data: JSON.stringify({
          "languageCode": "en-US",
          "queryInput": speechToText,
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
import fetch from 'node-fetch';

const url = "https://kompassapi.shinystat.com/cgi-bin/kimpress.cgi?company=NLC9987504,NLC9987242";

fetch(url, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(async response => {
  if (!response.ok) {
    throw new Error('Network response was not ok ' + response.statusText);
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  } else {
    return response.text();
  }
})
.then(data => {
  if (typeof data === 'string') {
    console.log('Received text data:', data);
  } else {
    console.log('Received JSON data:', data);
  }
})
.catch(error => {
  console.error('There has been a problem with your fetch operation:', error);
});

let currentFontScale=1.0,speechEnabled=false,focusModeActive=false,readingGuideActive=false,guideColor='#667eea',guideThickness=4,calmingAudioEl=null;
function toggleAccessMenu(){var m=document.getElementById('accessMenuInline');if(!m)return;m.style.display=m.style.display==='flex'?'none':'flex'}
function toggleDarkMode(){document.body.classList.toggle('light-mode')}
function toggleDyslexiaMode(){document.body.classList.toggle('dyslexia-mode');localStorage.setItem('fontFamily',document.body.classList.contains('dyslexia-mode')?'dyslexic':'default')}
function increaseTextSize(){currentFontScale=Math.min(currentFontScale+0.1,1.5);document.body.style.fontSize=(currentFontScale*100)+'%'}
function decreaseTextSize(){currentFontScale=Math.max(currentFontScale-0.1,0.8);document.body.style.fontSize=(currentFontScale*100)+'%'}

function toggleReadingGuidePanel(){
  readingGuideActive=!readingGuideActive;
  var g=document.getElementById('readingGuideBar'),p=document.getElementById('guideSettingsPanel');
  if(readingGuideActive){
    if(!g){
      g=document.createElement('div');g.id='readingGuideBar';
      g.style.cssText='position:fixed;left:0;right:0;pointer-events:none;z-index:99999;display:block;';
      document.body.appendChild(g);
      document.addEventListener('mousemove',moveGuide);
    }
    updateGuide();g.style.display='block';
    if(!p){
      p=document.createElement('div');p.id='guideSettingsPanel';p.className='guide-settings-panel';
      var h='<h4>Reading Guide</h4>';
      h+='<span class="thickness-label">Colour:</span><div class="color-options">';
      var cols=['#667eea','#ef4444','#22c55e','#eab308','#ec4899','#ffffff'];
      cols.forEach(function(c,i){
        h+='<div class="color-option'+(i===0?' selected':'')+'" style="background:'+c+'" data-color="'+c+'"></div>';
      });
      h+='</div>';
      h+='<span class="thickness-label">Thickness: <span id="thickVal">4px</span></span>';
      h+='<input type="range" class="thickness-slider" min="2" max="20" value="4">';
      p.innerHTML=h;
      document.body.appendChild(p);
      p.querySelectorAll('.color-option').forEach(function(el){
        el.addEventListener('click',function(){
          setGColor(this.getAttribute('data-color'),this);
        });
      });
      p.querySelector('.thickness-slider').addEventListener('input',function(){
        setGThick(this.value);
      });
    }
    p.style.display='block';
  }else{
    if(g)g.style.display='none';
    if(p)p.style.display='none';
    document.removeEventListener('mousemove',moveGuide);
  }
}
function moveGuide(e){var g=document.getElementById('readingGuideBar');if(g&&readingGuideActive)g.style.top=(e.clientY-guideThickness/2)+'px'}
function updateGuide(){var g=document.getElementById('readingGuideBar');if(!g)return;g.style.height=guideThickness+'px';g.style.background='linear-gradient(90deg,transparent,'+guideColor+',transparent)';g.style.boxShadow='0 0 20px '+guideColor+'60'}
function setGColor(c,el){guideColor=c;updateGuide();document.querySelectorAll('.color-option').forEach(function(o){o.classList.remove('selected')});if(el)el.classList.add('selected')}
function setGThick(v){guideThickness=parseInt(v);updateGuide();var l=document.getElementById('thickVal');if(l)l.textContent=v+'px'}


function toggleTextToSpeech(){
  speechEnabled=!speechEnabled;
  if(speechEnabled){
    document.body.style.cursor='help';
    document.addEventListener('click',handleTTS);
    spk('Text to speech enabled. Click any text to hear it.');
  }else{
    document.body.style.cursor='';
    document.removeEventListener('click',handleTTS);
    window.speechSynthesis.cancel();
  }
}
function handleTTS(e){
  if(!speechEnabled)return;
  if(['BUTTON','INPUT','TEXTAREA','SELECT'].indexOf(e.target.tagName)>=0)return;
  if(window.speechSynthesis.speaking){window.speechSynthesis.cancel();document.querySelectorAll('.tts-reading').forEach(function(el){el.classList.remove('tts-reading')});return}
  var el=e.target;
  while(el&&el!==document.body){if(['P','DIV','LI','TD','H1','H2','H3','H4','SPAN','LABEL'].indexOf(el.tagName)>=0)break;el=el.parentElement}
  var t=(el||e.target).innerText;
  if(t&&t.trim().length>2){el.classList.add('tts-reading');var u=new SpeechSynthesisUtterance(t.substring(0,800));u.rate=0.9;u.onend=function(){el.classList.remove('tts-reading')};window.speechSynthesis.speak(u)}
}
function spk(t){var u=new SpeechSynthesisUtterance(t);u.rate=0.9;window.speechSynthesis.speak(u)}

function toggleHighContrast(){document.body.classList.toggle('high-contrast')}

function toggleFocusMode(){
  focusModeActive=!focusModeActive;
  if(focusModeActive){
    document.querySelectorAll('.cred-box').forEach(function(el,i){if(i>0){el.style.opacity='0.15';el.style.transition='opacity 0.3s'}});
  }else{
    document.querySelectorAll('.cred-box').forEach(function(el){el.style.opacity='1'});
  }
}


function toggleCalmingAudio(){
  if(!calmingAudioEl){
    calmingAudioEl=document.createElement('audio');
    calmingAudioEl.loop=true;calmingAudioEl.volume=0.3;
    calmingAudioEl.innerHTML='<source src="/static/audio/adhd_calm.mp3" type="audio/mpeg"><source src="/static/audio/relax_sleep.mp3" type="audio/mpeg">';
    document.body.appendChild(calmingAudioEl);
    var c=document.createElement('div');c.id='audioControlPanel';c.className='audio-control-panel';
    c.innerHTML='<span style="color:#e2e8f0;font-size:13px">Calming Audio</span><input type="range" min="0" max="100" value="30" style="width:100px;accent-color:#667eea" id="volSlider"><button id="stopAudioBtn" style="background:#991b1b;color:#fff;border:none;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px">Stop</button>';
    document.body.appendChild(c);
    document.getElementById('volSlider').addEventListener('input',function(){if(calmingAudioEl)calmingAudioEl.volume=this.value/100});
    document.getElementById('stopAudioBtn').addEventListener('click',function(){toggleCalmingAudio()});
  }
  if(calmingAudioEl.paused){
    calmingAudioEl.play().then(function(){var c=document.getElementById('audioControlPanel');if(c)c.style.display='flex'}).catch(function(e){console.error('Audio:',e)});
  }else{
    calmingAudioEl.pause();var c=document.getElementById('audioControlPanel');if(c)c.style.display='none';
  }
}


function toggleVoiceInput(){
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){alert('Voice input not supported. Try Chrome.');return}
  var r=new SR();r.lang='en-GB';
  r.onresult=function(e){var t=e.results[0][0].transcript;var i=document.getElementById('chatInput');if(i){i.value=t;i.focus()}};
  r.start();
}


function resetAccessibility(){
  document.body.classList.remove('dyslexia-mode','high-contrast','light-mode');
  document.body.style.fontSize='';document.body.style.cursor='';
  currentFontScale=1.0;speechEnabled=false;
  document.removeEventListener('click',handleTTS);
  window.speechSynthesis.cancel();
  if(calmingAudioEl)calmingAudioEl.pause();
  var ac=document.getElementById('audioControlPanel');if(ac)ac.style.display='none';
  readingGuideActive=false;
  var g=document.getElementById('readingGuideBar');if(g)g.style.display='none';
  var gp=document.getElementById('guideSettingsPanel');if(gp)gp.style.display='none';
  document.removeEventListener('mousemove',moveGuide);
  focusModeActive=false;
  document.querySelectorAll('.cred-box').forEach(function(el){el.style.opacity='1'});
  var m=document.getElementById('accessMenuInline');if(m)m.style.display='none';
}


(function(){
  var f=localStorage.getItem('fontFamily');
  if(f==='dyslexic')document.body.classList.add('dyslexia-mode');
  var s=localStorage.getItem('fontSize');
  if(s){currentFontScale=parseFloat(s)/100;document.body.style.fontSize=s+'%'}
})();

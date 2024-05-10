
export default {
data() {
return {
  user: '',
  password: ''
};
},
methods: {
login(payload) {
console.log("Test");
  const path = 'http://localhost:5000/login';
  axios.post(path, payload)
    .catch((error) => {

      console.log(error);
    });
},
handleAddSubmit() {
  const payload = {
    user: this.user,
    password: this.password
  };
  this.login(payload);
  this.initForm();
},
initForm() {
  this.user = '';
  this.password = '';
},
}
};
import { checkLoginStatus } from '../services/facebookAuth';

const FacebookLoginButton = ({ onLoginSuccess }) => {

  const checkLoginState = () => {
    window.FB.getLoginStatus(function(response) {
      if (response.status === 'connected') {
        // Utilisateur connecté avec succès
        onLoginSuccess(response.authResponse);
      }
    });
  };

  return (
    <div>
      <fb:login-button
        scope="public_profile,email"
        onlogin="checkLoginState();">
      </fb:login-button>
    </div>
  );
};

export default FacebookLoginButton;
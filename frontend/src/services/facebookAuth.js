// Vérifie si l'utilisateur est connecté à Facebook
export const checkLoginStatus = () => {
    return new Promise((resolve) => {
      window.FB.getLoginStatus(function(response) {
        resolve(response);
      });
    });
  };
  
  // Connecter l'utilisateur Facebook
  export const loginWithFacebook = () => {
    return new Promise((resolve) => {
      window.FB.login(function(response) {
        resolve(response);
      }, { scope: 'public_profile,email' });
    });
  };
  
  // Déconnecter l'utilisateur
  export const logoutFromFacebook = () => {
    return new Promise((resolve) => {
      window.FB.logout(function(response) {
        resolve(response);
      });
    });
  };
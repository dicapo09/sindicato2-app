package cl.sindicato.pacificodelsur;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

/**
 * Notificaciones push de la directiva.
 * Con la app cerrada o en segundo plano, Android muestra el aviso solo (canal «avisos»).
 * Con la app abierta, Firebase entrega el mensaje aquí y lo mostramos nosotros.
 */
public class Avisos extends FirebaseMessagingService {
    static final String CANAL = "avisos";

    /** Crea el canal de notificaciones (Android 8+). Se puede llamar varias veces. */
    static void crearCanal(Context c) {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        if (nm == null || nm.getNotificationChannel(CANAL) != null) return;
        NotificationChannel ch = new NotificationChannel(CANAL, "Avisos del sindicato", NotificationManager.IMPORTANCE_HIGH);
        ch.setDescription("Informativos, citaciones y encuestas publicados por la directiva");
        nm.createNotificationChannel(ch);
    }

    @Override
    public void onMessageReceived(RemoteMessage msg) {
        String titulo = null, texto = null;
        if (msg.getNotification() != null) {
            titulo = msg.getNotification().getTitle();
            texto = msg.getNotification().getBody();
        }
        if (titulo == null) titulo = msg.getData().get("titulo");
        if (texto == null) texto = msg.getData().get("texto");
        if (titulo == null && texto == null) return;

        crearCanal(this);
        Intent abrir = new Intent(this, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent pi = PendingIntent.getActivity(this, 0, abrir, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);

        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, CANAL) : new Notification.Builder(this);
        b.setSmallIcon(R.drawable.ic_aviso)
                .setColor(getColor(R.color.aviso))
                .setContentTitle(titulo != null ? titulo : "Sindicato N°2")
                .setContentText(texto)
                .setStyle(new Notification.BigTextStyle().bigText(texto))
                .setAutoCancel(true)
                .setContentIntent(pi);
        if (Build.VERSION.SDK_INT < 26) b.setPriority(Notification.PRIORITY_HIGH);

        NotificationManager nm = getSystemService(NotificationManager.class);
        if (nm != null) nm.notify((int) (System.currentTimeMillis() & 0x7fffffff), b.build());
    }

    @Override
    public void onNewToken(String token) {
        // Usamos temas (topics), así que no hace falta guardar el token en ningún servidor.
    }
}

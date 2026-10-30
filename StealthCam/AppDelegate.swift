import UIKit

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        let window = UIWindow(frame: UIScreen.main.bounds)
        window.rootViewController = ViewController()
        window.makeKeyAndVisible()
        self.window = window
        return true
    }

    // Hàm này sẽ bắt các link URL từ Phím tắt (Shortcuts) để tự động chọn đúng chế độ quay
    func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {
        guard let vc = window?.rootViewController as? ViewController else { return false }
        
        // Lấy tên chế độ từ URL (ví dụ: stealthcam://slomo05 -> slomo05)
        let mode = url.host ?? "cam12"
        
        // Dừng camera hiện tại và khởi động lại với thông số đúng yêu cầu
        vc.captureSession?.stopRunning()
        vc.setupCamera(mode: mode)
        
        return true
    }
}
